import asyncio 
import logging
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..model.orm import Bill, BillProposer, BillStatus, Member, MemberBillStatistic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemberRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_members(self, limit: int = 20, age: Optional[str] = None, party: Optional[str] = None, committee: Optional[str] = None) -> list:
        """
        의원 목록 조회 
        """
        stmt = select(Member.MEMBER_ID)

        if party:
            stmt = stmt.where(Member.PLPT_NM == party)
        if age:
            stmt = stmt.where(Member.GTELT_ERACO.like(f"%{age}%"))
        if committee:
            stmt = stmt.where(Member.BLNG_CMIT_NM.like(f"%{committee}%"))

        stmt = stmt.order_by(Member.NAAS_NM.asc()).limit(limit)

        try:
            members = await self.db.execute(stmt)
        except ValueError:
            logger.warning("Members not found")
            return None
        except Exception as e:
            logger.error("Unexpected error fetching members", e)
            return None
        
        result = await self._get_members_info_batch_optimized([member.MEMBER_ID for member in members])
        return result

    async def get_member_by_id(self, member_id: str) -> Member:
        """
        의원 ID로 의원 정보 조회
        """
        stmt = select(Member).where(Member.MEMBER_ID == member_id)
        try: 
            result = await self.db.execute(stmt)
        except ValueError:
            logger.warning(f"Member ID: {member_id} not found")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching member {member_id}", e)
            return None

        member = result.scalar_one_or_none()
        if not member:
            logger.warning(f"Member with ID {member_id} not found")
            return None
        return member

    async def get_member_info(self, member_id: str) -> dict:
        """
        의원 종합 정보 단일 쿼리
        """
        base_stmt = (
            select(
                Member,
                MemberBillStatistic,
                MemberBillStatistic,
                MemberBillStatistic,
            )
            .select_from(Member)
            .join(MemberBillStatistic, Member.MEMBER_ID == MemberBillStatistic.MEMBER_ID)
            .where(Member.MEMBER_ID == member_id)
        )
        
        committee_stmt = (
            select(
                Bill.COMMITTEE_NAME.label("active_committee"),
                func.count(BillProposer.BILL_ID).label("total_count"),
                func.sum(case((BillProposer.RST == 1, 1), else_=0)).label("lead_count"),
                func.sum(case((BillProposer.RST == 0, 1), else_=0)).label("co_count"),
            )
            .select_from(BillProposer)
            .join(Bill, Bill.BILL_ID == BillProposer.BILL_ID)
            .where(BillProposer.MEMBER_ID == member_id)
            .group_by(Bill.COMMITTEE_NAME)
            .order_by(func.count(BillProposer.BILL_ID).desc())
            .limit(3)
        )
        
        base_result, committee_result = await asyncio.gather(
            self.db.execute(base_stmt),
            self.db.execute(committee_stmt)
        )
        
        base_data = base_result.first()
        if not base_data:
            logger.warning(f"Member with ID {member_id} not found")
            return None
        committee_data = committee_result.all()
        
        return {
            "member": base_data[0],
            "bill_stats": base_data[1],
            "committee_stats": [
                {
                    "active_committee": cs.active_committee,
                    "total_count": cs.total_count,
                    "lead_count": cs.lead_count,
                    "co_count": cs.co_count,
                }
                for cs in committee_data
            ]
        }
        
    async def get_top_members_by_criteria(self, criteria: str, party: Optional[str] = None, committee: Optional[str] = None, limit: int = 10) -> list[str]:
        """
        특정 기준으로 상위 의원 조회
        """
        member_stmt = select(Member)
        if party:
            member_stmt = member_stmt.where(Member.PLPT_NM == party)
        if committee:
            member_stmt = member_stmt.where(Member.BLNG_CMIT_NM.like(f"%{committee}%"))
        
        criteria_mappig = {
            "total_count": MemberBillStatistic.total_count,
            "total_pass_rate": MemberBillStatistic.total_pass_rate,
            "lead_count": MemberBillStatistic.lead_count,
            "lead_pass_rate": MemberBillStatistic.lead_pass_rate,
            "co_count": MemberBillStatistic.co_count,
            "co_pass_rate": MemberBillStatistic.co_pass_rate,
        }

        criteria_column = criteria_mappig[criteria]
        stmt = (
            select(MemberBillStatistic.MEMBER_ID)
            .order_by(criteria_column.desc())
            .limit(limit)
        )
        
        try: 
            members = await self.db.execute(stmt)
        except Exception as e:
            logger.error(f"Unexpected error fetching committee stats, member {member_id}", e)
            return None
        
        result = await self._get_members_info_batch_optimized([member.MEMBER_ID for member in members])
        return result
    
    async def _get_members_info_batch_optimized(self, member_ids: list[str]) -> dict:
        """
        배치 처리 최적화
        - IN 절 사용으로 DB 라운드트립 최소화
        """
        # async with self.monitor.measure_time(f"Batch Query for {len(member_ids)} members"):
        #     if not member_ids:
        #         return {}
            
        # 모든 의원 정보를 한 번에 조회
        member_stmt = select(Member).where(Member.MEMBER_ID.in_(member_ids))
        stats_stmt = select(MemberBillStatistic).where(
            MemberBillStatistic.MEMBER_ID.in_(member_ids)
        )
        
        # 위원회 통계는 윈도우 함수 사용
        committee_stmt = (
            select(
                BillProposer.MEMBER_ID,
                Bill.COMMITTEE_NAME.label("active_committee"),
                func.count(BillProposer.BILL_ID).label("total_count"),
                func.sum(case((BillProposer.RST == 1, 1), else_=0)).label("lead_count"),
                func.sum(case((BillProposer.RST == 0, 1), else_=0)).label("co_count"),
                func.row_number().over(
                    partition_by=BillProposer.MEMBER_ID,
                    order_by=func.count(BillProposer.BILL_ID).desc()
                ).label("rank")
            )
            .select_from(BillProposer)
            .join(Bill, Bill.BILL_ID == BillProposer.BILL_ID)
            .where(BillProposer.MEMBER_ID.in_(member_ids))
            .group_by(BillProposer.MEMBER_ID, Bill.COMMITTEE_NAME)
        )
        
        # 병렬 실행
        member_result, stats_result, committee_result = await asyncio.gather(
            self.db.execute(member_stmt),
            self.db.execute(stats_stmt),
            self.db.execute(committee_stmt)
        )
        
        # 결과를 딕셔너리로 변환
        members = {m.MEMBER_ID: m for m in member_result.scalars()}
        stats = {s.MEMBER_ID: s for s in stats_result.scalars()}
        
        # 위원회 데이터 그룹화 (상위 3개만)
        committees = {}
        for row in committee_result:
            if row.rank <= 3:  # 상위 3개만
                if row.MEMBER_ID not in committees:
                    committees[row.MEMBER_ID] = []
                committees[row.MEMBER_ID].append({
                    "active_committee": row.active_committee,
                    "total_count": row.total_count,
                    "lead_count": row.lead_count,
                    "co_count": row.co_count,
                })
        
        # 최종 결과 조합
        result = []
        for member_id in member_ids:
            if member_id in members:
                result.append({
                    "member": members[member_id],
                    "bill_stats": stats.get(member_id),
                    "committee_stats": committees.get(member_id, [])
                })
            else:
                logger.warning(f"Member {member_id} not found")
        return result

    async def search_members(self, 
                           name: Optional[str] = None,
                           party: Optional[str] = None,
                           committee: Optional[str] = None,
                           limit: int = 20) -> list[Member]:
        """
        복합 검색 조건으로 의원 검색
        """
        stmt = select(Member)
        
        conditions = []
        if name:
            conditions.append(Member.NAAS_NM.contains(name))
        if party:
            conditions.append(Member.PLPT_NM == party)
        if committee:
            conditions.append(Member.CMIT_NM == committee)
        
        if conditions:
            stmt = stmt.where(*conditions)
        
        stmt = stmt.order_by(Member.NAAS_NM.asc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()


class BillRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_top_bills_by_criteria(self,
                                        criteria: str = "proposed",
                                        committee: Optional[str] = None,
                                        limit: int = 10,
                                        ) -> list[dict]:
        """
        특정 기준으로 상위 의안 조회
        """
        
        if criteria == "proposed":
            stmt = (
                select(
                    Bill.BILL_NAME, 
                    func.count(Bill.BILL_ID).label("bill_count")
                )
                .group_by(Bill.BILL_NAME)
                .order_by(func.count(Bill.BILL_ID).desc())
                .limit(limit)
            )
        elif criteria == "passed":
            stmt = (
                select(
                    Bill.BILL_NAME, 
                    func.count(Bill.BILL_ID).label("bill_count")
                )
                .where(Bill.STATUS.in_([BillStatus.ORIGINAL_PASSED, BillStatus.AMENDED_PASSED]))
                .group_by(Bill.BILL_NAME)  # BILL_ID 대신 BILL_NAME으로 수정
                .order_by(func.count(Bill.BILL_ID).desc())
                .limit(limit)
            )
        elif criteria == "proposed_by_committee":
            if not committee:
                raise ValueError("Committee name is required for this criteria")
            stmt = (
                select(
                    Bill.BILL_NAME, 
                    func.count(Bill.BILL_ID).label("bill_count")
                )
                .where(Bill.COMMITTEE_NAME == committee)
                .group_by(Bill.BILL_NAME)
                .order_by(func.count(Bill.BILL_ID).desc())
                .limit(limit)
            )
        else:
            raise ValueError("Invalid criteria for top bills")
        
        result = await self.db.execute(stmt)
        top_bills = result.all()
        
        logger.info(f"Top bills by {criteria}: {len(top_bills)} results")
        
        return [
            {"bill_name": bill.BILL_NAME, "bill_count": bill.bill_count} 
            for bill in top_bills
        ]

    async def get_bill_by_id(self, bill_id: str) -> Bill:
        """
        의안 ID로 의안 정보 조회
        """
        stmt = select(Bill).where(Bill.BILL_ID == bill_id)
        result = await self.db.execute(stmt)
        bill = result.scalar_one_or_none()
        
        if not bill:
            raise ValueError(f"Bill with ID {bill_id} not found")
        return bill

    async def get_bills_by_member(self, member_id: str, limit: int = 10) -> list[Bill]:
        """
        특정 의원이 제안한 의안 목록 조회
        """
        stmt = (
            select(Bill)
            .join(BillProposer, Bill.BILL_ID == BillProposer.BILL_ID)
            .where(BillProposer.MEMBER_ID == member_id)
            .order_by(Bill.PRPS_DT.desc())  # 제안일자 내림차순
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_bills_by_status(self, status: BillStatus, limit: int = 10) -> list[Bill]:
        """
        특정 상태의 의안 목록 조회
        """
        stmt = (
            select(Bill)
            .where(Bill.STATUS == status)
            .order_by(Bill.PRPS_DT.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_bill_statistics(self) -> dict:
        """
        전체 의안 통계 조회
        """
        # 총 의안 수
        total_stmt = select(func.count(Bill.BILL_ID))
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar()
        
        # 상태별 의안 수
        status_stmt = (
            select(
                Bill.STATUS,
                func.count(Bill.BILL_ID).label("count")
            )
            .group_by(Bill.STATUS)
        )
        status_result = await self.db.execute(status_stmt)
        status_stats = {row.STATUS: row.count for row in status_result.all()}
        
        # 위원회별 의안 수
        committee_stmt = (
            select(
                Bill.COMMITTEE_NAME,
                func.count(Bill.BILL_ID).label("count")
            )
            .group_by(Bill.COMMITTEE_NAME)
            .order_by(func.count(Bill.BILL_ID).desc())
            .limit(10)
        )
        committee_result = await self.db.execute(committee_stmt)
        committee_stats = [
            {"committee": row.COMMITTEE_NAME, "count": row.count}
            for row in committee_result.all()
        ]
        
        return {
            "total_count": total_count,
            "status_distribution": status_stats,
            "top_committees": committee_stats,
        }


# ==========================================
# 사용 예시 및 의존성 주입
# ==========================================

class RepositoryFactory:
    """
    Repository 팩토리 클래스
    """
    @staticmethod
    def create_member_repository(db_session: AsyncSession) -> MemberRepository:
        return MemberRepository(db_session)

    @staticmethod
    def create_bill_repository(db_session: AsyncSession) -> BillRepository:
        return BillRepository(db_session)


# ==========================================
# 성능 최적화된 버전
# ==========================================

class OptimizedMemberRepository(MemberRepository):
    """
    성능 최적화된 MemberRepository
    """
    
    async def get_member_with_preloaded_relations(self, member_id: str) -> Member:
        """관계를 미리 로드하여 N+1 문제 방지"""
        stmt = (
            select(Member)
            .options(
                selectinload(Member.bills),  # 관계가 정의되어 있다면
                # selectinload(Member.committees)  # 필요한 관계들 추가
            )
            .where(Member.MEMBER_ID == member_id)
        )
        
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")
        return member
    
    async def get_members_with_pagination(self, 
                                        page: int = 1, 
                                        page_size: int = 20,
                                        **filters) -> dict:
        offset = (page - 1) * page_size
        
        # 기본 쿼리
        base_stmt = select(Member)
        count_stmt = select(func.count(Member.MEMBER_ID))
        
        # 필터 적용
        if filters.get('party'):
            base_stmt = base_stmt.where(Member.PLPT_NM == filters['party'])
            count_stmt = count_stmt.where(Member.PLPT_NM == filters['party'])
        
        # 데이터와 총 개수를 병렬로 조회
        data_stmt = base_stmt.offset(offset).limit(page_size)
        
        data_result, count_result = await asyncio.gather(
            self.db.execute(data_stmt),
            self.db.execute(count_stmt)
        )
        
        members = data_result.scalars().all()
        total_count = count_result.scalar()
        
        return {
            "items": members,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }

# =====================================
    async def get_member_bill_statistics(self, member_id: str) -> MemberBillStatistic:
        """
        의원 통계 정보 조회
        """
        stmt = select(MemberBillStatistic).where(MemberBillStatistic.MEMBER_ID == member_id)
        
        try: 
            result = await self.db.execute(stmt)
        except Exception as e:
            logger.error(f"Unexpected error fetching committee stats, member {member_id}", e)
            return None

        member_stats = result.scalar_one_or_none()
        if not member_stats:
            logger.warning(f"Member with ID {member_id} not found")
            return None
        return member_stats

    async def get_member_committee_statistics(self, member_id: str) -> list[dict]:
        """
        의원의 위원회 통계 정보 조회
        """
        stmt = (
            select(
                Bill.COMMITTEE_NAME.label("active_committee"),
                func.count(BillProposer.BILL_ID).label("total_count"),
                func.sum(case((BillProposer.RST == 1, 1), else_=0)).label("lead_count"),
                func.sum(case((BillProposer.RST == 0, 1), else_=0)).label("co_count"),
            )
            .select_from(BillProposer)
            .join(Bill, Bill.BILL_ID == BillProposer.BILL_ID)
            .where(BillProposer.MEMBER_ID == member_id)
            .group_by(Bill.COMMITTEE_NAME)
            .order_by(func.count(BillProposer.BILL_ID).desc())
            .limit(3)
        )
        
        try: 
            result = await self.db.execute(stmt)
        except Exception as e:
            logger.error(f"Unexpected error fetching committee stats, member {member_id}", e)
            return None
        data = result.all()
        
        return [
            {
                "active_committee": cs.active_committee,
                "total_count": cs.total_count,
                "lead_count": cs.lead_count,
                "co_count": cs.co_count,
            }
            for cs in data
        ]