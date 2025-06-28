from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# 모델 import (사용자가 제공한 모델들)
from model.orm import Bill, BillDetail, BillProposer, BillStatus, Committee, Member
from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload


class MemberBillStatisticsCalculator:
    """의원별 의안 통계 계산기"""

    def __init__(self, db_session: Session):
        self.db = db_session

        # 의안 상태별 분류
        self.passed_statuses = [BillStatus.ORIGINAL_PASSED, BillStatus.AMENDED_PASSED]

        self.pending_statuses = [
            BillStatus.COMMITTEE_PENDING,
            BillStatus.LEGISLATION_PENDING,
            BillStatus.COMMITTEE_IN_PROGRESS,
            BillStatus.LEGISLATION_IN_PROGRESS,
            BillStatus.WAITING,
        ]

        self.rejected_statuses = [
            BillStatus.WITHDRAWN,
            BillStatus.REJECTED,
            BillStatus.AMENDED_DISCARDED,
            BillStatus.ALTERNATIVE_DISCARDED,
        ]

    def calculate_member_statistics(
        self, member_id: str
    ) -> Optional[MemberBillStatistics]:
        """특정 의원의 통계 계산"""

        # 의원 정보 조회
        member = self.db.query(Member).filter(Member.MEMBER_ID == member_id).first()
        if not member:
            return None

        # 전체 발의 의안 통계
        total_stats = self._calculate_total_statistics(member_id)

        # 대표발의 통계
        lead_stats = self._calculate_lead_statistics(member_id)

        # 공동발의 통계
        co_stats = self._calculate_co_statistics(member_id)

        # 가장 활발한 위원회 찾기
        most_active_committee, most_active_ratio = self._find_most_active_committee(
            member_id
        )

        return MemberBillStatistics(
            member_id=member.MEMBER_ID,
            member_name=member.NAAS_NM,
            total_proposed_bills=total_stats["total_count"],
            total_pass_rate=total_stats["pass_rate"],
            most_active_committee=most_active_committee,
            most_active_committee_ratio=most_active_ratio,
            lead_proposed_count=lead_stats["total_count"],
            lead_pass_rate=lead_stats["pass_rate"],
            lead_pending_rate=lead_stats["pending_rate"],
            lead_committee_stats=lead_stats["committee_stats"],
            co_proposed_count=co_stats["total_count"],
            co_pass_rate=co_stats["pass_rate"],
            co_pending_rate=co_stats["pending_rate"],
            co_committee_stats=co_stats["committee_stats"],
        )

    def calculate_all_members_statistics(self) -> List[MemberBillStatistics]:
        """모든 의원의 통계 계산"""
        members = self.db.query(Member).all()
        statistics = []

        for member in members:
            stats = self.calculate_member_statistics(member.MEMBER_ID)
            if stats:
                statistics.append(stats)

        return statistics

    def _calculate_total_statistics(self, member_id: str) -> Dict:
        """전체 발의 의안 통계 계산"""

        # 전체 발의 의안 조회 (대표 + 공동)
        total_bills_query = (
            self.db.query(Bill)
            .join(BillProposer)
            .filter(BillProposer.MEMBER_ID == member_id)
        )

        total_count = total_bills_query.count()

        if total_count == 0:
            return {"total_count": 0, "pass_rate": 0.0}

        # 통과된 의안 수
        passed_count = total_bills_query.filter(
            Bill.STATUS.in_(self.passed_statuses)
        ).count()

        pass_rate = (passed_count / total_count) * 100 if total_count > 0 else 0.0

        return {"total_count": total_count, "pass_rate": round(pass_rate, 2)}

    def _calculate_lead_statistics(self, member_id: str) -> Dict:
        """대표발의 통계 계산"""

        # 대표발의 의안 조회
        lead_bills_query = (
            self.db.query(Bill)
            .join(BillProposer)
            .filter(and_(BillProposer.MEMBER_ID == member_id, BillProposer.RST == True))
        )

        total_count = lead_bills_query.count()

        if total_count == 0:
            return {
                "total_count": 0,
                "pass_rate": 0.0,
                "pending_rate": 0.0,
                "committee_stats": [],
            }

        # 상태별 집계
        status_counts = self._get_status_counts(lead_bills_query)

        # 위원회별 통계
        committee_stats = self._get_committee_statistics(lead_bills_query)

        return {
            "total_count": total_count,
            "pass_rate": status_counts["pass_rate"],
            "pending_rate": status_counts["pending_rate"],
            "committee_stats": committee_stats,
        }

    def _calculate_co_statistics(self, member_id: str) -> Dict:
        """공동발의 통계 계산"""

        # 공동발의 의안 조회
        co_bills_query = (
            self.db.query(Bill)
            .join(BillProposer)
            .filter(
                and_(BillProposer.MEMBER_ID == member_id, BillProposer.RST == False)
            )
        )

        total_count = co_bills_query.count()

        if total_count == 0:
            return {
                "total_count": 0,
                "pass_rate": 0.0,
                "pending_rate": 0.0,
                "committee_stats": [],
            }

        # 상태별 집계
        status_counts = self._get_status_counts(co_bills_query)

        # 위원회별 통계
        committee_stats = self._get_committee_statistics(co_bills_query)

        return {
            "total_count": total_count,
            "pass_rate": status_counts["pass_rate"],
            "pending_rate": status_counts["pending_rate"],
            "committee_stats": committee_stats,
        }

    def _get_status_counts(self, bills_query) -> Dict:
        """의안 상태별 개수 및 비율 계산"""

        total_count = bills_query.count()

        if total_count == 0:
            return {"pass_rate": 0.0, "pending_rate": 0.0}

        # 통과된 의안
        passed_count = bills_query.filter(Bill.STATUS.in_(self.passed_statuses)).count()

        # 계류 중인 의안
        pending_count = bills_query.filter(
            Bill.STATUS.in_(self.pending_statuses)
        ).count()

        pass_rate = (passed_count / total_count) * 100
        pending_rate = (pending_count / total_count) * 100

        return {
            "pass_rate": round(pass_rate, 2),
            "pending_rate": round(pending_rate, 2),
        }

    def _get_committee_statistics(self, bills_query) -> List[CommitteeStats]:
        """위원회별 통계 계산"""

        # select() 구문을 명시적으로 사용
        bill_ids_select = select(Bill.BILL_ID).select_from(bills_query.subquery())

        committee_results = (
            self.db.query(
                Bill.COMMITTEE_NAME,
                func.count(Bill.BILL_ID).label("total_bills"),
                func.sum(
                    case((Bill.STATUS.in_(self.passed_statuses), 1), else_=0)
                ).label("passed_bills"),
                func.sum(
                    case((Bill.STATUS.in_(self.pending_statuses), 1), else_=0)
                ).label("pending_bills"),
            )
            .filter(Bill.BILL_ID.in_(bill_ids_select))
            .filter(Bill.COMMITTEE_NAME.isnot(None))
            .group_by(Bill.COMMITTEE_NAME)
            .all()
        )

        committee_stats = []
        for result in committee_results:
            total = result.total_bills
            passed = result.passed_bills or 0
            pending = result.pending_bills or 0

            pass_rate = (passed / total) * 100 if total > 0 else 0
            pending_rate = (pending / total) * 100 if total > 0 else 0

            committee_stats.append(
                CommitteeStats(
                    committee_name=result.COMMITTEE_NAME,
                    total_bills=total,
                    passed_bills=passed,
                    pending_bills=pending,
                    pass_rate=round(pass_rate, 2),
                    pending_rate=round(pending_rate, 2),
                )
            )

        # 의안 수 기준으로 내림차순 정렬
        committee_stats.sort(key=lambda x: x.total_bills, reverse=True)

        return committee_stats

    def _find_most_active_committee(self, member_id: str) -> Tuple[str, float]:
        """가장 활발하게 활동한 위원회 찾기"""

        # 위원회별 발의 의안 수 집계
        committee_counts = (
            self.db.query(
                Bill.COMMITTEE_NAME, func.count(Bill.BILL_ID).label("bill_count")
            )
            .join(BillProposer)
            .filter(BillProposer.MEMBER_ID == member_id)
            .filter(Bill.COMMITTEE_NAME.isnot(None))
            .group_by(Bill.COMMITTEE_NAME)
            .order_by(func.count(Bill.BILL_ID).desc())
            .all()
        )

        if not committee_counts:
            return "", 0.0

        # 전체 발의 의안 수
        total_bills = sum(count.bill_count for count in committee_counts)

        # 가장 많은 위원회
        most_active = committee_counts[0]
        ratio = (most_active.bill_count / total_bills) * 100 if total_bills > 0 else 0

        return most_active.COMMITTEE_NAME, round(ratio, 2)

    def get_top_members_by_criteria(
        self, criteria: str = "total_bills", limit: int = 10
    ) -> List[MemberBillStatistics]:
        """특정 기준으로 상위 의원 조회"""

        all_stats = self.calculate_all_members_statistics()

        sort_key_map = {
            "total_bills": lambda x: x.total_proposed_bills,
            "total_pass_rate": lambda x: x.total_pass_rate,
            "lead_bills": lambda x: x.lead_proposed_count,
            "lead_pass_rate": lambda x: x.lead_pass_rate,
            "co_bills": lambda x: x.co_proposed_count,
            "co_pass_rate": lambda x: x.co_pass_rate,
        }

        sort_key = sort_key_map.get(criteria, sort_key_map["total_bills"])

        sorted_stats = sorted(all_stats, key=sort_key, reverse=True)

        return sorted_stats[:limit]


# ============ 사용 예시 및 유틸리티 함수 ============


def print_member_statistics(stats: MemberBillStatistics):
    """의원 통계를 보기 좋게 출력"""

    print(f"\n{'='*50}")
    print(f"의원명: {stats.member_name} ({stats.member_id})")
    print(f"{'='*50}")

    print(f"\n📊 전체 발의 의안 통계")
    print(f"  • 총 발의 의안: {stats.total_proposed_bills}건")
    print(f"  • 전체 통과율: {stats.total_pass_rate}%")
    print(
        f"  • 가장 활발한 위원회: {stats.most_active_committee} ({stats.most_active_committee_ratio}%)"
    )

    print(f"\n🎯 대표발의 통계")
    print(f"  • 대표발의 건수: {stats.lead_proposed_count}건")
    print(f"  • 대표발의 통과율: {stats.lead_pass_rate}%")
    print(f"  • 대표발의 계류율: {stats.lead_pending_rate}%")

    if stats.lead_committee_stats:
        print(f"  • 위원회별 대표발의 현황:")
        for committee_stat in stats.lead_committee_stats[:5]:  # 상위 5개만 표시
            print(
                f"    - {committee_stat.committee_name}: {committee_stat.total_bills}건 "
                f"(통과율: {committee_stat.pass_rate}%)"
            )

    print(f"\n🤝 공동발의 통계")
    print(f"  • 공동발의 건수: {stats.co_proposed_count}건")
    print(f"  • 공동발의 통과율: {stats.co_pass_rate}%")
    print(f"  • 공동발의 계류율: {stats.co_pending_rate}%")

    if stats.co_committee_stats:
        print(f"  • 위원회별 공동발의 현황:")
        for committee_stat in stats.co_committee_stats[:5]:  # 상위 5개만 표시
            print(
                f"    - {committee_stat.committee_name}: {committee_stat.total_bills}건 "
                f"(통과율: {committee_stat.pass_rate}%)"
            )


def export_statistics_to_dict(stats: MemberBillStatistics) -> Dict:
    """통계를 딕셔너리로 변환 (JSON 내보내기용)"""

    return {
        "member_info": {"member_id": stats.member_id, "member_name": stats.member_name},
        "total_statistics": {
            "total_proposed_bills": stats.total_proposed_bills,
            "total_pass_rate": stats.total_pass_rate,
            "most_active_committee": stats.most_active_committee,
            "most_active_committee_ratio": stats.most_active_committee_ratio,
        },
        "lead_statistics": {
            "count": stats.lead_proposed_count,
            "pass_rate": stats.lead_pass_rate,
            "pending_rate": stats.lead_pending_rate,
            "committee_breakdown": [
                {
                    "committee_name": cs.committee_name,
                    "total_bills": cs.total_bills,
                    "passed_bills": cs.passed_bills,
                    "pending_bills": cs.pending_bills,
                    "pass_rate": cs.pass_rate,
                    "pending_rate": cs.pending_rate,
                }
                for cs in stats.lead_committee_stats
            ],
        },
        "co_statistics": {
            "count": stats.co_proposed_count,
            "pass_rate": stats.co_pass_rate,
            "pending_rate": stats.co_pending_rate,
            "committee_breakdown": [
                {
                    "committee_name": cs.committee_name,
                    "total_bills": cs.total_bills,
                    "passed_bills": cs.passed_bills,
                    "pending_bills": cs.pending_bills,
                    "pass_rate": cs.pass_rate,
                    "pending_rate": cs.pending_rate,
                }
                for cs in stats.co_committee_stats
            ],
        },
    }


# ============ 사용 예시 ============


def main_example(db_session: Session):
    """사용 예시"""

    calculator = MemberBillStatisticsCalculator(db_session)

    # 1. 특정 의원 통계 계산
    member_stats = calculator.calculate_member_statistics("MP001")
    if member_stats:
        print_member_statistics(member_stats)

    # 2. 전체 발의 의안 수 기준 상위 10명
    print("\n🏆 총 발의 의안 수 상위 10명")
    top_by_total = calculator.get_top_members_by_criteria("total_bills", 10)
    for i, stats in enumerate(top_by_total, 1):
        print(f"{i:2d}. {stats.member_name}: {stats.total_proposed_bills}건")

    # 3. 통과율 기준 상위 10명 (최소 10건 이상 발의한 의원만)
    print("\n🎯 통과율 상위 10명 (최소 10건 이상 발의)")
    top_by_pass_rate = [
        stats
        for stats in calculator.get_top_members_by_criteria("total_pass_rate", 50)
        if stats.total_proposed_bills >= 10
    ][:10]

    for i, stats in enumerate(top_by_pass_rate, 1):
        print(
            f"{i:2d}. {stats.member_name}: {stats.total_pass_rate}% "
            f"({stats.total_proposed_bills}건 중)"
        )

    # 4. 대표발의 건수 상위 10명
    print("\n👑 대표발의 건수 상위 10명")
    top_by_lead = calculator.get_top_members_by_criteria("lead_bills", 10)
    for i, stats in enumerate(top_by_lead, 1):
        print(f"{i:2d}. {stats.member_name}: {stats.lead_proposed_count}건")
