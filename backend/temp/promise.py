import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import requests
from fuzzywuzzy import fuzz


class PromiseStatus(Enum):
    """공약 이행 상태"""

    NOT_STARTED = "미착수"
    IN_PROGRESS = "추진중"
    COMPLETED = "완료"
    POSTPONED = "연기"
    ABANDONED = "포기"
    MODIFIED = "수정"


class PromiseCategory(Enum):
    """공약 분야"""

    ECONOMY = "경제"
    EDUCATION = "교육"
    WELFARE = "복지"
    ENVIRONMENT = "환경"
    DEFENSE = "국방"
    FOREIGN_AFFAIRS = "외교"
    JUSTICE = "사법"
    ADMINISTRATION = "행정"
    CULTURE = "문화"
    HEALTH = "보건"
    AGRICULTURE = "농업"
    LABOR = "노동"
    OTHER = "기타"


@dataclass
class Promise:
    """개별 공약 정보"""

    id: str
    title: str
    content: str
    category: PromiseCategory
    keywords: List[str]
    target_date: Optional[str] = None
    specific_bill_names: List[str] = field(default_factory=list)
    priority: int = 1  # 1(높음) ~ 5(낮음)
    measurable: bool = True  # 측정 가능 여부

    # 추적 정보
    status: PromiseStatus = PromiseStatus.NOT_STARTED
    progress_score: float = 0.0  # 0~100
    related_bills: List[str] = field(default_factory=list)
    related_activities: List[str] = field(default_factory=list)
    last_updated: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )


@dataclass
class PromiseProgress:
    """공약 이행 진척도"""

    promise_id: str
    activity_type: str  # 'bill', 'speech', 'committee', 'seminar' 등
    activity_id: str
    activity_title: str
    relevance_score: float  # 0~1, 공약과의 관련성
    contribution_score: float  # 0~1, 이행에 대한 기여도
    date: str
    description: str = ""


class PromiseDataManager:
    """공약 데이터 관리자"""

    def __init__(self):
        self.promises: Dict[str, Promise] = {}
        self.progress_records: List[PromiseProgress] = []

    def load_promises_from_csv(self, csv_file: str):
        """CSV 파일에서 공약 데이터 로드"""
        try:
            df = pd.read_csv(csv_file, encoding="utf-8-sig")

            for _, row in df.iterrows():
                keywords = [
                    k.strip()
                    for k in str(row.get("키워드", "")).split(",")
                    if k.strip()
                ]
                bill_names = [
                    b.strip()
                    for b in str(row.get("관련법안", "")).split(",")
                    if b.strip()
                ]

                promise = Promise(
                    id=str(row["공약ID"]),
                    title=str(row["공약제목"]),
                    content=str(row["공약내용"]),
                    category=PromiseCategory(row.get("분야", "OTHER")),
                    keywords=keywords,
                    target_date=str(row.get("목표일", "")),
                    specific_bill_names=bill_names,
                    priority=int(row.get("우선순위", 3)),
                    measurable=bool(row.get("측정가능", True)),
                )

                self.promises[promise.id] = promise

        except Exception as e:
            print(f"공약 데이터 로드 실패: {e}")

    def load_promises_from_json(self, json_file: str):
        """JSON 파일에서 공약 데이터 로드"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for promise_data in data.get("promises", []):
                promise = Promise(**promise_data)
                self.promises[promise.id] = promise

        except Exception as e:
            print(f"공약 데이터 로드 실패: {e}")

    def add_promise(self, promise: Promise):
        """공약 추가"""
        self.promises[promise.id] = promise

    def get_promises_by_category(self, category: PromiseCategory) -> List[Promise]:
        """분야별 공약 조회"""
        return [p for p in self.promises.values() if p.category == category]

    def save_promises_to_json(self, json_file: str):
        """공약 데이터를 JSON으로 저장"""
        data = {
            "promises": [promise.__dict__ for promise in self.promises.values()],
            "progress_records": [record.__dict__ for record in self.progress_records],
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class PromiseTracker:
    """공약 이행도 추적기"""

    def __init__(self, data_manager: PromiseDataManager, api_client):
        self.data_manager = data_manager
        self.api_client = api_client

        # 키워드 가중치 설정
        self.keyword_weights = {
            "exact_match": 1.0,  # 정확한 키워드 일치
            "partial_match": 0.7,  # 부분 일치
            "semantic_match": 0.5,  # 의미적 유사성
            "category_match": 0.3,  # 분야 일치
        }

    def track_bill_promises(self, member_name: str) -> Dict[str, List[PromiseProgress]]:
        """법안 발의를 통한 공약 이행 추적"""
        bills = self.api_client.get_bills_by_member(member_name)
        promise_progress = defaultdict(list)

        for promise in self.data_manager.promises.values():
            for bill in bills:
                relevance_score = self._calculate_bill_relevance(promise, bill)

                if relevance_score > 0.3:  # 임계값 이상만 포함
                    progress = PromiseProgress(
                        promise_id=promise.id,
                        activity_type="bill",
                        activity_id=bill.get("BILL_ID", ""),
                        activity_title=bill.get("BILL_NM", ""),
                        relevance_score=relevance_score,
                        contribution_score=self._calculate_bill_contribution(bill),
                        date=bill.get("PPSL_DT", ""),
                        description=f"법안 발의: {bill.get('BILL_NM', '')}",
                    )

                    promise_progress[promise.id].append(progress)

        return dict(promise_progress)

    def track_speech_promises(
        self, member_name: str
    ) -> Dict[str, List[PromiseProgress]]:
        """회의 발언을 통한 공약 이행 추적"""
        speeches = self.api_client.get_plenary_minutes(member_name)
        speeches.extend(self.api_client.get_committee_minutes(member_name))

        promise_progress = defaultdict(list)

        for promise in self.data_manager.promises.values():
            for speech in speeches:
                relevance_score = self._calculate_speech_relevance(promise, speech)

                if relevance_score > 0.4:  # 발언은 더 높은 임계값
                    progress = PromiseProgress(
                        promise_id=promise.id,
                        activity_type="speech",
                        activity_id=speech.get("MEETING_ID", ""),
                        activity_title=f"회의 발언 ({speech.get('MTGDT', '')})",
                        relevance_score=relevance_score,
                        contribution_score=0.3,  # 발언은 상대적으로 낮은 기여도
                        date=speech.get("MTGDT", ""),
                        description=f"회의 발언에서 공약 관련 내용 언급",
                    )

                    promise_progress[promise.id].append(progress)

        return dict(promise_progress)

    def track_seminar_promises(
        self, member_name: str
    ) -> Dict[str, List[PromiseProgress]]:
        """정책 세미나를 통한 공약 이행 추적"""
        seminars = self.api_client.get_policy_seminars(member_name)
        promise_progress = defaultdict(list)

        for promise in self.data_manager.promises.values():
            for seminar in seminars:
                relevance_score = self._calculate_seminar_relevance(promise, seminar)

                if relevance_score > 0.3:
                    progress = PromiseProgress(
                        promise_id=promise.id,
                        activity_type="seminar",
                        activity_id=seminar.get("SEMINAR_ID", ""),
                        activity_title=seminar.get("SEMINAR_NM", ""),
                        relevance_score=relevance_score,
                        contribution_score=0.6,  # 세미나는 중간 기여도
                        date=seminar.get("SEMINAR_DT", ""),
                        description=f"정책 세미나 개최: {seminar.get('SEMINAR_NM', '')}",
                    )

                    promise_progress[promise.id].append(progress)

        return dict(promise_progress)

    def _calculate_bill_relevance(self, promise: Promise, bill: Dict) -> float:
        """법안과 공약의 관련성 점수 계산"""
        score = 0.0
        bill_title = bill.get("BILL_NM", "").lower()
        bill_summary = bill.get("BILL_SUMMARY", "").lower()

        # 1. 특정 법안명 직접 매칭
        for specific_bill in promise.specific_bill_names:
            if fuzz.ratio(specific_bill.lower(), bill_title) > 80:
                return 1.0  # 직접 매칭시 최고점

        # 2. 키워드 매칭
        for keyword in promise.keywords:
            keyword_lower = keyword.lower()

            # 제목에서 정확 매칭
            if keyword_lower in bill_title:
                score += self.keyword_weights["exact_match"]
            # 제목에서 부분 매칭
            elif fuzz.partial_ratio(keyword_lower, bill_title) > 70:
                score += self.keyword_weights["partial_match"]

            # 요약에서 매칭 (있는 경우)
            if bill_summary and keyword_lower in bill_summary:
                score += self.keyword_weights["semantic_match"]

        # 3. 분야별 매칭 (위원회 기준)
        bill_committee = bill.get("JRCMIT_NM", "")
        if self._is_related_committee(promise.category, bill_committee):
            score += self.keyword_weights["category_match"]

        return min(score, 1.0)  # 최대 1.0으로 제한

    def _calculate_speech_relevance(self, promise: Promise, speech: Dict) -> float:
        """발언과 공약의 관련성 점수 계산"""
        score = 0.0
        speech_content = speech.get("SPEAK_CONT", "").lower()

        if not speech_content:
            return 0.0

        # 키워드 기반 매칭
        for keyword in promise.keywords:
            keyword_lower = keyword.lower()

            # 발언 내용에서 키워드 등장 횟수
            keyword_count = speech_content.count(keyword_lower)
            if keyword_count > 0:
                score += min(keyword_count * 0.2, 0.8)  # 최대 0.8점

        return min(score, 1.0)

    def _calculate_seminar_relevance(self, promise: Promise, seminar: Dict) -> float:
        """세미나와 공약의 관련성 점수 계산"""
        score = 0.0
        seminar_title = seminar.get("SEMINAR_NM", "").lower()
        seminar_topic = seminar.get("SEMINAR_TOPIC", "").lower()

        # 키워드 매칭
        for keyword in promise.keywords:
            keyword_lower = keyword.lower()

            if keyword_lower in seminar_title:
                score += 0.8
            elif keyword_lower in seminar_topic:
                score += 0.6
            elif fuzz.partial_ratio(keyword_lower, seminar_title) > 70:
                score += 0.4

        return min(score, 1.0)

    def _calculate_bill_contribution(self, bill: Dict) -> float:
        """법안의 공약 이행 기여도 계산"""
        # 법안 상태에 따른 기여도
        status = bill.get("RGS_CONF_RSLT", "")

        contribution_map = {
            "가결": 1.0,  # 완전 이행
            "부결": 0.2,  # 시도했지만 실패
            "계류": 0.6,  # 진행 중
            "폐기": 0.1,  # 거의 기여 없음
        }

        return contribution_map.get(status, 0.5)  # 기본값 0.5

    def _is_related_committee(
        self, promise_category: PromiseCategory, committee_name: str
    ) -> bool:
        """공약 분야와 위원회의 관련성 판단"""
        committee_mapping = {
            PromiseCategory.ECONOMY: ["기획재정", "산업통상자원", "중소벤처기업"],
            PromiseCategory.EDUCATION: ["교육", "과학기술정보방송통신"],
            PromiseCategory.WELFARE: ["보건복지", "여성가족"],
            PromiseCategory.ENVIRONMENT: ["환경노동"],
            PromiseCategory.DEFENSE: ["국방"],
            PromiseCategory.FOREIGN_AFFAIRS: ["외교통일"],
            PromiseCategory.JUSTICE: ["법제사법"],
            PromiseCategory.ADMINISTRATION: ["행정안전", "정무"],
            PromiseCategory.CULTURE: ["문화체육관광"],
            PromiseCategory.AGRICULTURE: ["농림축산식품해양수산"],
            PromiseCategory.LABOR: ["환경노동"],
        }

        related_committees = committee_mapping.get(promise_category, [])
        return any(related in committee_name for related in related_committees)


class PromiseAnalyzer:
    """공약 이행도 분석기"""

    def __init__(self, tracker: PromiseTracker):
        self.tracker = tracker

    def calculate_overall_fulfillment_rate(self, member_name: str) -> Dict:
        """전체 공약 이행률 계산"""
        # 모든 활동에서 공약 관련 진척도 수집
        bill_progress = self.tracker.track_bill_promises(member_name)
        speech_progress = self.tracker.track_speech_promises(member_name)
        seminar_progress = self.tracker.track_seminar_promises(member_name)

        # 공약별 종합 점수 계산
        promise_scores = {}
        total_promises = len(self.tracker.data_manager.promises)

        for promise_id, promise in self.tracker.data_manager.promises.items():
            score = 0.0

            # 법안 기여도
            if promise_id in bill_progress:
                bill_score = sum(
                    p.relevance_score * p.contribution_score
                    for p in bill_progress[promise_id]
                )
                score += min(bill_score, 0.7)  # 법안 최대 70%

            # 발언 기여도
            if promise_id in speech_progress:
                speech_score = sum(
                    p.relevance_score * p.contribution_score
                    for p in speech_progress[promise_id]
                )
                score += min(speech_score, 0.2)  # 발언 최대 20%

            # 세미나 기여도
            if promise_id in seminar_progress:
                seminar_score = sum(
                    p.relevance_score * p.contribution_score
                    for p in seminar_progress[promise_id]
                )
                score += min(seminar_score, 0.3)  # 세미나 최대 30%

            # 우선순위 가중치 적용
            weight = 1.0 / promise.priority  # 우선순위가 높을수록 가중치 증가
            promise_scores[promise_id] = min(score * weight, 1.0)

            # Promise 객체 업데이트
            promise.progress_score = promise_scores[promise_id] * 100
            if promise.progress_score >= 80:
                promise.status = PromiseStatus.COMPLETED
            elif promise.progress_score >= 40:
                promise.status = PromiseStatus.IN_PROGRESS

        # 전체 이행률 계산
        overall_rate = (
            sum(promise_scores.values()) / total_promises * 100
            if total_promises > 0
            else 0
        )

        return {
            "overall_fulfillment_rate": overall_rate,
            "completed_promises": sum(
                1 for score in promise_scores.values() if score >= 0.8
            ),
            "in_progress_promises": sum(
                1 for score in promise_scores.values() if 0.4 <= score < 0.8
            ),
            "not_started_promises": sum(
                1 for score in promise_scores.values() if score < 0.4
            ),
            "total_promises": total_promises,
            "promise_scores": promise_scores,
            "detailed_progress": {
                "bills": bill_progress,
                "speeches": speech_progress,
                "seminars": seminar_progress,
            },
        }

    def analyze_by_category(self, member_name: str) -> Dict[PromiseCategory, Dict]:
        """분야별 공약 이행률 분석"""
        overall_analysis = self.calculate_overall_fulfillment_rate(member_name)
        promise_scores = overall_analysis["promise_scores"]

        category_analysis = {}

        for category in PromiseCategory:
            category_promises = self.tracker.data_manager.get_promises_by_category(
                category
            )

            if not category_promises:
                continue

            category_scores = [promise_scores.get(p.id, 0) for p in category_promises]
            avg_score = sum(category_scores) / len(category_scores) * 100

            category_analysis[category] = {
                "fulfillment_rate": avg_score,
                "total_promises": len(category_promises),
                "completed": sum(1 for score in category_scores if score >= 0.8),
                "in_progress": sum(
                    1 for score in category_scores if 0.4 <= score < 0.8
                ),
                "not_started": sum(1 for score in category_scores if score < 0.4),
                "promise_details": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "score": promise_scores.get(p.id, 0) * 100,
                        "status": p.status.value,
                    }
                    for p in category_promises
                ],
            }

        return category_analysis

    def generate_fulfillment_report(self, member_name: str) -> str:
        """공약 이행도 종합 보고서 생성"""
        overall_analysis = self.calculate_overall_fulfillment_rate(member_name)
        category_analysis = self.analyze_by_category(member_name)

        report = f"""
{'='*80}
국회의원 공약 이행도 분석 보고서
{'='*80}

📊 전체 이행 현황
- 전체 이행률: {overall_analysis['overall_fulfillment_rate']:.1f}%
- 총 공약 수: {overall_analysis['total_promises']}개
- 완료된 공약: {overall_analysis['completed_promises']}개 ({overall_analysis['completed_promises']/overall_analysis['total_promises']*100:.1f}%)
- 추진 중인 공약: {overall_analysis['in_progress_promises']}개 ({overall_analysis['in_progress_promises']/overall_analysis['total_promises']*100:.1f}%)
- 미착수 공약: {overall_analysis['not_started_promises']}개 ({overall_analysis['not_started_promises']/overall_analysis['total_promises']*100:.1f}%)

📈 분야별 이행 현황
"""

        for category, analysis in category_analysis.items():
            if analysis["total_promises"] > 0:
                report += f"""
🏷️ {category.value}
- 이행률: {analysis['fulfillment_rate']:.1f}%
- 공약 수: {analysis['total_promises']}개
- 완료: {analysis['completed']}개, 추진중: {analysis['in_progress']}개, 미착수: {analysis['not_started']}개

주요 공약:"""

                # 상위 3개 공약 표시
                top_promises = sorted(
                    analysis["promise_details"], key=lambda x: x["score"], reverse=True
                )[:3]

                for i, promise in enumerate(top_promises, 1):
                    report += f"""
  {i}. {promise['title'][:50]}{'...' if len(promise['title']) > 50 else ''}
     이행도: {promise['score']:.1f}% ({promise['status']})"""

        report += f"\n\n{'='*80}\n"

        return report


# 사용 예시와 샘플 데이터
def create_sample_promises() -> PromiseDataManager:
    """샘플 공약 데이터 생성"""
    manager = PromiseDataManager()

    # 샘플 공약들
    sample_promises = [
        Promise(
            id="P001",
            title="국민연금 보장성 강화법 발의",
            content="국민연금 급여 인상 및 수급 연령 조정을 통한 노후 보장성 강화",
            category=PromiseCategory.WELFARE,
            keywords=["국민연금", "급여", "보장성", "노후"],
            specific_bill_names=["국민연금법 일부개정법률안"],
            priority=1,
        ),
        Promise(
            id="P002",
            title="재생에너지 확대 정책 추진",
            content="태양광, 풍력 등 재생에너지 비중을 2030년까지 30%로 확대",
            category=PromiseCategory.ENVIRONMENT,
            keywords=["재생에너지", "태양광", "풍력", "친환경"],
            priority=2,
        ),
        Promise(
            id="P003",
            title="청년 일자리 창출 지원",
            content="청년 고용 확대를 위한 기업 지원 정책 및 창업 지원 강화",
            category=PromiseCategory.ECONOMY,
            keywords=["청년", "일자리", "고용", "창업"],
            priority=1,
        ),
    ]

    for promise in sample_promises:
        manager.add_promise(promise)

    return manager


def main():
    """메인 실행 함수"""
    # API 키 설정
    API_KEY = "YOUR_API_KEY_HERE"

    # 시스템 초기화
    api_client = NationalAssemblyAPI(API_KEY)  # 이전 코드의 API 클라이언트 재사용

    # 샘플 공약 데이터 생성
    promise_manager = create_sample_promises()

    # 공약 추적기 및 분석기 초기화
    tracker = PromiseTracker(promise_manager, api_client)
    analyzer = PromiseAnalyzer(tracker)

    # 분석할 의원
    member_name = "홍길동"

    try:
        # 공약 이행도 분석 실행
        print(f"의원 '{member_name}'의 공약 이행도 분석 중...")

        # 종합 분석
        fulfillment_analysis = analyzer.calculate_overall_fulfillment_rate(member_name)

        # 분야별 분석
        category_analysis = analyzer.analyze_by_category(member_name)

        # 보고서 생성
        report = analyzer.generate_fulfillment_report(member_name)
        print(report)

        # 상세 결과 출력
        print("📋 상세 분석 결과:")
        print(f"- 전체 이행률: {fulfillment_analysis['overall_fulfillment_rate']:.1f}%")
        print(
            f"- 법안 관련 활동: {len(fulfillment_analysis['detailed_progress']['bills'])}건"
        )
        print(
            f"- 발언 관련 활동: {len(fulfillment_analysis['detailed_progress']['speeches'])}건"
        )
        print(
            f"- 세미나 관련 활동: {len(fulfillment_analysis['detailed_progress']['seminars'])}건"
        )

        # 공약 데이터 저장
        promise_manager.save_promises_to_json(f"{member_name}_promises_analysis.json")

    except Exception as e:
        print(f"공약 이행도 분석 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
