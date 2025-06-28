import json
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


# ==================== ENUMS ====================
class PolicyArea(Enum):
    """정책 분야"""

    ECONOMY = "경제"
    WELFARE = "복지"
    EDUCATION = "교육"
    ENVIRONMENT = "환경"
    SECURITY = "국방"
    FOREIGN_AFFAIRS = "외교"
    JUSTICE = "사법"
    ADMINISTRATION = "행정"
    CULTURE = "문화"
    HEALTH = "보건"
    AGRICULTURE = "농업"
    LABOR = "노동"
    TRANSPORTATION = "교통"
    COMMUNICATION = "통신"
    WOMEN_FAMILY = "여성가족"
    OTHER = "기타"


class ActivityType(Enum):
    """활동 유형"""

    BILL = "법안"
    SPEECH = "발언"
    VOTING = "표결"
    AUDIT = "국감"
    SEMINAR = "세미나"
    SNS = "SNS"


class IdeologySpectrum(Enum):
    """이념 스펙트럼"""

    VERY_PROGRESSIVE = "매우진보"
    PROGRESSIVE = "진보"
    MODERATE = "중도"
    CONSERVATIVE = "보수"
    VERY_CONSERVATIVE = "매우보수"


# ==================== COMPUTED DATA STRUCTURES ====================
@dataclass
class LegislativeMetrics:
    """입법 활동 지표 (계산됨)"""

    member_name: str

    # 발의 건수
    representative_bills_count: int = 0
    co_sponsored_bills_count: int = 0
    total_bills_count: int = 0

    # 통과율
    passed_bills_count: int = 0
    pending_bills_count: int = 0
    rejected_bills_count: int = 0
    bill_passage_rate: float = 0.0  # %

    # 처리 기간
    avg_processing_days: float = 0.0
    median_processing_days: float = 0.0
    fastest_processing_days: int = 0
    slowest_processing_days: int = 0

    # 분야별 전문성
    area_specialization: Dict[PolicyArea, float] = field(default_factory=dict)
    primary_area: Optional[PolicyArea] = None
    specialization_score: float = 0.0  # 집중도 점수

    # 시계열 데이터
    monthly_bills: Dict[str, int] = field(default_factory=dict)  # YYYY-MM: count

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")  # (start_date, end_date)


@dataclass
class VotingMetrics:
    """표결 참여 지표 (계산됨)"""

    member_name: str

    # 참여율
    total_votes: int = 0
    participated_votes: int = 0
    participation_rate: float = 0.0  # %

    # 표결 패턴
    agree_votes: int = 0
    disagree_votes: int = 0
    abstain_votes: int = 0
    absent_votes: int = 0

    agree_rate: float = 0.0  # %
    disagree_rate: float = 0.0  # %
    abstain_rate: float = 0.0  # %

    # 정당 일치도
    party_alignment_rate: float = 0.0  # %
    cross_party_votes: int = 0  # 당론과 다른 표결

    # 주요 법안 표결 참여
    major_bill_votes: int = 0
    major_bill_participation_rate: float = 0.0  # %

    # 시계열 데이터
    monthly_participation: Dict[str, Tuple[int, int]] = field(
        default_factory=dict
    )  # YYYY-MM: (participated, total)

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class MeetingMetrics:
    """회의 활동 지표 (계산됨)"""

    member_name: str

    # 발언 횟수
    plenary_speeches: int = 0
    committee_speeches: int = 0
    total_speeches: int = 0

    # 발언 길이
    avg_speech_length: float = 0.0  # 글자 수
    total_speech_length: int = 0
    longest_speech_length: int = 0

    # 질의 활동
    question_count: int = 0
    interpellation_count: int = 0  # 국정감사 질의

    # 위원회별 활동
    committee_activity: Dict[str, int] = field(
        default_factory=dict
    )  # 위원회명: 발언횟수
    primary_committee: str = ""

    # 주제별 발언 분석
    topic_distribution: Dict[str, float] = field(default_factory=dict)  # 주제: 비율

    # 시계열 데이터
    monthly_speeches: Dict[str, int] = field(default_factory=dict)  # YYYY-MM: count

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class AuditMetrics:
    """국정감사 활동 지표 (계산됨)"""

    member_name: str

    # 질의 활동
    total_questions: int = 0
    total_question_time: int = 0  # 분
    avg_question_time: float = 0.0  # 분

    # 감사 성과
    findings_count: int = 0
    follow_up_requests: int = 0
    improvement_suggestions: int = 0

    # 감사 대상 기관
    audited_agencies: List[str] = field(default_factory=list)
    agency_diversity_score: float = 0.0  # 다양성 점수

    # 분야별 감사 활동
    audit_areas: Dict[PolicyArea, int] = field(default_factory=dict)
    primary_audit_area: Optional[PolicyArea] = None

    # 시계열 데이터
    yearly_audit_activity: Dict[str, Dict[str, int]] = field(
        default_factory=dict
    )  # YYYY: {questions, findings}

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class PolicyMetrics:
    """정책 활동 지표 (계산됨)"""

    member_name: str

    # 세미나 활동
    seminars_hosted: int = 0
    seminar_participants_total: int = 0
    avg_participants_per_seminar: float = 0.0

    # SNS 활동
    sns_posts_total: int = 0
    sns_engagement_total: int = 0  # 좋아요+공유+댓글
    avg_engagement_per_post: float = 0.0

    # 플랫폼별 활동
    platform_activity: Dict[str, int] = field(default_factory=dict)  # 플랫폼: 게시물수
    most_active_platform: str = ""

    # 입법예고 참여
    legislative_preview_participation: int = 0

    # 정책 영역별 활동
    policy_area_activity: Dict[PolicyArea, int] = field(default_factory=dict)

    # 시계열 데이터
    monthly_policy_activity: Dict[str, Dict[str, int]] = field(
        default_factory=dict
    )  # YYYY-MM: {seminars, sns}

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class PromiseFulfillmentMetrics:
    """공약 이행도 지표 (계산됨)"""

    member_name: str

    # 전체 이행 현황
    total_promises: int = 0
    completed_promises: int = 0
    in_progress_promises: int = 0
    not_started_promises: int = 0
    overall_fulfillment_rate: float = 0.0  # %

    # 분야별 이행률
    area_fulfillment_rates: Dict[PolicyArea, float] = field(default_factory=dict)
    best_performing_area: Optional[PolicyArea] = None
    worst_performing_area: Optional[PolicyArea] = None

    # 우선순위별 이행률
    priority_fulfillment_rates: Dict[int, float] = field(
        default_factory=dict
    )  # 우선순위: 이행률

    # 개별 공약 점수
    promise_scores: Dict[str, float] = field(
        default_factory=dict
    )  # promise_id: score(0-1)

    # 활동별 기여도
    bill_contribution: float = 0.0  # 법안을 통한 기여도
    speech_contribution: float = 0.0  # 발언을 통한 기여도
    seminar_contribution: float = 0.0  # 세미나를 통한 기여도

    # 시계열 진척도
    monthly_progress: Dict[str, float] = field(
        default_factory=dict
    )  # YYYY-MM: 누적 이행률

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class SpecializationProfile:
    """전문성 프로필 (계산됨)"""

    member_name: str

    # 전문 분야 순위 (상위 5개)
    specialization_ranking: List[Tuple[PolicyArea, float]] = field(
        default_factory=list
    )  # (분야, 점수)
    primary_specialization: Optional[PolicyArea] = None
    specialization_diversity: float = 0.0  # 다양성 점수 (0-1)

    # 일관성 지표
    consistency_score: float = 0.0  # 시간에 걸친 일관성
    activity_concentration: float = 0.0  # 활동 집중도

    # 깊이 지표
    depth_score: float = 0.0  # 실질적 기여도
    impact_score: float = 0.0  # 정책 영향력

    # 시간별 전문성 변화
    specialization_timeline: Dict[str, Dict[PolicyArea, float]] = field(
        default_factory=dict
    )  # YYYY-MM: {분야: 점수}

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class IdeologyProfile:
    """이념 프로필 (계산됨)"""

    member_name: str

    # 종합 이념 점수
    overall_ideology_score: float = 0.0  # -1(진보) ~ +1(보수)
    ideology_classification: IdeologySpectrum = IdeologySpectrum.MODERATE

    # 세부 이념 점수
    economic_ideology: float = 0.0  # 경제 이념
    social_ideology: float = 0.0  # 사회 이념
    security_ideology: float = 0.0  # 안보 이념

    # 활동별 이념 점수
    bill_ideology_score: float = 0.0  # 법안 기반
    speech_ideology_score: float = 0.0  # 발언 기반
    voting_ideology_score: float = 0.0  # 표결 기반

    # 정당 일치도
    party_loyalty_score: float = 0.0  # 정당 노선 일치도
    independent_voting_rate: float = 0.0  # 독립적 표결 비율

    # 이념적 키워드 분석
    progressive_keywords_usage: int = 0
    conservative_keywords_usage: int = 0
    keyword_ideology_ratio: float = 0.0  # 보수키워드/진보키워드 비율

    # 시간별 이념 변화
    ideology_timeline: Dict[str, float] = field(
        default_factory=dict
    )  # YYYY-MM: 이념점수

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class InterestProfile:
    """관심 분야 프로필 (계산됨)"""

    member_name: str

    # 핵심 관심사 (상위 20개)
    core_interests: List[Tuple[str, float]] = field(
        default_factory=list
    )  # (키워드, 관심도)
    primary_interest: str = ""

    # 관심사 다양성
    interest_diversity_score: float = 0.0  # 0-1
    focus_concentration: float = 0.0  # 집중도

    # 시간별 관심 변화 (6개 구간)
    interest_timeline: Dict[str, List[float]] = field(
        default_factory=dict
    )  # 키워드: [구간1, 구간2, ...]
    emerging_interests: List[str] = field(default_factory=list)  # 새로 부상한 관심사
    declining_interests: List[str] = field(default_factory=list)  # 관심이 줄어든 분야

    # 활동 패턴
    monthly_activity_volume: Dict[str, int] = field(
        default_factory=dict
    )  # YYYY-MM: 총 활동량
    activity_consistency: float = 0.0  # 활동의 일관성

    # 관심 분야별 활동 분포
    area_activity_distribution: Dict[PolicyArea, float] = field(
        default_factory=dict
    )  # 분야: 비율

    # 계산 메타데이터
    calculation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


# ==================== VIEW DATA STRUCTURES ====================


@dataclass
class MemberPerformanceView:
    """의원 성과 종합 뷰 (표시용)"""

    member_name: str
    party_name: str
    district: str
    term_number: int

    # 핵심 지표 요약
    overall_score: float = 0.0  # 종합 점수 (0-100)
    performance_grade: str = "C"  # A, B, C, D, F
    ranking_in_party: int = 0
    ranking_overall: int = 0

    # 주요 성과 지표
    legislative_score: float = 0.0  # 입법 점수
    voting_score: float = 0.0  # 표결 점수
    meeting_score: float = 0.0  # 회의 점수
    audit_score: float = 0.0  # 국감 점수
    policy_score: float = 0.0  # 정책 점수
    promise_score: float = 0.0  # 공약 점수

    # 특성 요약
    primary_specialization: str = ""
    ideology_label: str = ""
    activity_level: str = ""  # 활발/보통/저조

    # 강점/약점 분석
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)

    # 시각화용 데이터
    radar_chart_data: Dict[str, float] = field(default_factory=dict)  # 분야별 점수
    trend_data: Dict[str, List[float]] = field(default_factory=dict)  # 시계열 트렌드

    # 생성 메타데이터
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    data_period: Tuple[str, str] = ("", "")


@dataclass
class ComparisonView:
    """비교 분석 뷰 (표시용)"""

    comparison_type: str  # party/district/term/custom
    members: List[str] = field(default_factory=list)

    # 비교 테이블 데이터
    comparison_table: List[Dict[str, Any]] = field(default_factory=list)

    # 순위 데이터
    rankings: Dict[str, List[Tuple[str, float]]] = field(
        default_factory=dict
    )  # 지표명: [(의원명, 점수)]

    # 통계적 비교
    statistical_summary: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )  # 지표명: {평균, 표준편차 등}

    # 시각화용 데이터
    chart_data: Dict[str, Any] = field(default_factory=dict)

    # 인사이트
    key_insights: List[str] = field(default_factory=list)
    notable_differences: List[str] = field(default_factory=list)

    # 생성 메타데이터
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TrendAnalysisView:
    """트렌드 분석 뷰 (표시용)"""

    member_name: str
    analysis_period: Tuple[str, str]  # (start_date, end_date)

    # 전반적 트렌드
    overall_trend: str = ""  # 상승/하락/안정
    trend_score: float = 0.0  # 트렌드 강도

    # 지표별 트렌드
    legislative_trend: Dict[str, Any] = field(default_factory=dict)
    voting_trend: Dict[str, Any] = field(default_factory=dict)
    meeting_trend: Dict[str, Any] = field(default_factory=dict)
    policy_trend: Dict[str, Any] = field(default_factory=dict)

    # 변곡점 분석
    turning_points: List[Dict[str, Any]] = field(
        default_factory=list
    )  # 중요한 변화 시점

    # 예측 데이터
    future_projection: Dict[str, List[float]] = field(default_factory=dict)  # 향후 전망

    # 시각화용 데이터
    timeline_chart_data: Dict[str, List[Tuple[str, float]]] = field(
        default_factory=dict
    )

    # 인사이트
    trend_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # 생성 메타데이터
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ==================== DATA CONTAINER ====================


@dataclass
class MemberAnalysisData:
    """의원 분석 데이터 컨테이너"""

    member_name: str

    # === RAW DATA ===
    raw_bills: List[RawBillData] = field(default_factory=list)
    raw_member_info: Optional[RawMemberData] = None
    raw_voting_by_bill: List[RawVotingByBillData] = field(default_factory=list)
    raw_plenary_voting: List[RawPlenaryVotingData] = field(default_factory=list)
    raw_plenary_minutes: List[RawPlenaryMinutesData] = field(default_factory=list)
    raw_committee_minutes: List[RawCommitteeMinutesData] = field(default_factory=list)
    raw_audit_reports: List[RawAuditReportData] = field(default_factory=list)
    raw_sns: List[RawSNSData] = field(default_factory=list)
    raw_legislative_preview: List[RawLegislativePreviewData] = field(
        default_factory=list
    )
    raw_policy_seminars: List[RawPolicySeminarData] = field(default_factory=list)
    raw_promises: List[RawPromiseData] = field(default_factory=list)

    # === COMPUTED DATA ===
    legislative_metrics: Optional[LegislativeMetrics] = None
    voting_metrics: Optional[VotingMetrics] = None
    meeting_metrics: Optional[MeetingMetrics] = None
    audit_metrics: Optional[AuditMetrics] = None
    policy_metrics: Optional[PolicyMetrics] = None
    promise_metrics: Optional[PromiseFulfillmentMetrics] = None
    specialization_profile: Optional[SpecializationProfile] = None
    ideology_profile: Optional[IdeologyProfile] = None
    interest_profile: Optional[InterestProfile] = None

    # === VIEW DATA ===
    performance_view: Optional[MemberPerformanceView] = None

    # === METADATA ===
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    data_completeness: Dict[str, float] = field(default_factory=dict)  # 데이터 완성도
    calculation_status: Dict[str, str] = field(default_factory=dict)  # 계산 상태

    def get_data_summary(self) -> Dict[str, int]:
        """데이터 요약 통계"""
        return {
            "bills": len(self.raw_bills),
            "voting_by_bill": len(self.raw_voting_by_bill),
            "plenary_voting": len(self.raw_plenary_voting),
            "plenary_minutes": len(self.raw_plenary_minutes),
            "committee_minutes": len(self.raw_committee_minutes),
            "audit_reports": len(self.raw_audit_reports),
            "sns_posts": len(self.raw_sns),
            "policy_seminars": len(self.raw_policy_seminars),
            "legislative_preview": len(self.raw_legislative_preview),
            "promises": len(self.raw_promises),
        }

    def is_analysis_complete(self) -> bool:
        """분석 완료 여부 확인"""
        required_metrics = [
            self.legislative_metrics,
            self.voting_metrics,
            self.meeting_metrics,
            self.policy_metrics,
        ]
        return all(metric is not None for metric in required_metrics)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (저장용)"""

        # dataclass를 dict로 변환하는 헬퍼 함수
        def dataclass_to_dict(obj):
            if obj is None:
                return None
            return {k: v for k, v in obj.__dict__.items()}

        return {
            "member_name": self.member_name,
            "raw_data": {
                "bills": [dataclass_to_dict(b) for b in self.raw_bills],
                "member_info": dataclass_to_dict(self.raw_member_info),
                "voting_by_bill": [
                    dataclass_to_dict(v) for v in self.raw_voting_by_bill
                ],
                "plenary_voting": [
                    dataclass_to_dict(v) for v in self.raw_plenary_voting
                ],
                "plenary_minutes": [
                    dataclass_to_dict(m) for m in self.raw_plenary_minutes
                ],
                "committee_minutes": [
                    dataclass_to_dict(m) for m in self.raw_committee_minutes
                ],
                "audit_reports": [dataclass_to_dict(a) for a in self.raw_audit_reports],
                "sns": [dataclass_to_dict(s) for s in self.raw_sns],
                "legislative_preview": [
                    dataclass_to_dict(l) for l in self.raw_legislative_preview
                ],
                "policy_seminars": [
                    dataclass_to_dict(s) for s in self.raw_policy_seminars
                ],
                "promises": [dataclass_to_dict(p) for p in self.raw_promises],
            },
            "computed_data": {
                "legislative_metrics": dataclass_to_dict(self.legislative_metrics),
                "voting_metrics": dataclass_to_dict(self.voting_metrics),
                "meeting_metrics": dataclass_to_dict(self.meeting_metrics),
                "audit_metrics": dataclass_to_dict(self.audit_metrics),
                "policy_metrics": dataclass_to_dict(self.policy_metrics),
                "promise_metrics": dataclass_to_dict(self.promise_metrics),
                "specialization_profile": dataclass_to_dict(
                    self.specialization_profile
                ),
                "ideology_profile": dataclass_to_dict(self.ideology_profile),
                "interest_profile": dataclass_to_dict(self.interest_profile),
            },
            "view_data": {"performance_view": dataclass_to_dict(self.performance_view)},
            "metadata": {
                "last_updated": self.last_updated,
                "data_completeness": self.data_completeness,
                "calculation_status": self.calculation_status,
            },
        }


# ==================== USAGE EXAMPLES ====================


def example_usage():
    """사용 예시"""

    # 1. 원시 데이터 생성 (실제 API 응답 형태)
    raw_bill = RawBillData(
        BILL_ID="PRC_Z2Q2F0A5O1N1Q0M3K1Y8L1V0L7",
        BILL_NAME="국민연금법 일부개정법률안",
        PROPOSER="홍길동",
        RST_PROPOSER="홍길동",
        PROPOSE_DT="20240315",
        COMMITTEE="보건복지위원회",
        PROC_RESULT="가결",
        DETAIL_LINK="https://likms.assembly.go.kr/bill/...",
    )

    # 2. 의원 정보 데이터
    raw_member = RawMemberData(
        NAAS_NM="홍길동",
        PLPT_NM="더불어민주당",
        ELECD_NM="서울 강남구 갑",
        GTELT_ERACO="21",
        BLNG_CMIT_NM="보건복지위원회",
        NAAS_TEL_NO="02-788-xxxx",
    )

    # 3. 의안별 표결 데이터
    raw_voting_by_bill = RawVotingByBillData(
        BILL_ID="PRC_Z2Q2F0A5O1N1Q0M3K1Y8L1V0L7",
        BILL_NM="국민연금법 일부개정법률안",
        DELENAM="홍길동",
        POLYNAM="더불어민주당",
        VOTE_RSLT="찬성",
        VOTE_DT="20240420",
    )

    # 4. 본회의 표결 데이터
    raw_plenary_voting = RawPlenaryVotingData(
        HG_NM="홍길동",
        POLY_NM="더불어민주당",
        ORIG_NM="서울 강남구 갑",
        VOTE_DATE="20240420",
        BILL_NAME="국민연금법 일부개정법률안",
        RESULT_VOTE_MOD="찬성",
        BILL_URL="https://likms.assembly.go.kr/bill/...",
        AGE="21",
    )

    # 4. 계산된 지표 생성
    legislative_metrics = LegislativeMetrics(
        member_name="홍길동",
        representative_bills_count=15,
        co_sponsored_bills_count=87,
        total_bills_count=102,
        passed_bills_count=12,
        bill_passage_rate=80.0,
        avg_processing_days=67.5,
        area_specialization={PolicyArea.WELFARE: 0.8, PolicyArea.HEALTH: 0.6},
        primary_area=PolicyArea.WELFARE,
        specialization_score=0.85,
    )

    # 5. 뷰 데이터 생성
    performance_view = MemberPerformanceView(
        member_name="홍길동",
        party_name="더불어민주당",
        district="서울 강남구 갑",
        term_number=21,
        overall_score=78.5,
        performance_grade="B+",
        ranking_in_party=15,
        ranking_overall=45,
        legislative_score=85.2,
        voting_score=92.1,
        meeting_score=68.7,
        primary_specialization="복지/사회보장",
        ideology_label="중도진보",
        activity_level="활발",
        strengths=["법안 통과율 높음", "복지 분야 전문성", "꾸준한 활동"],
        weaknesses=["국감 질의 부족", "SNS 소통 미흡"],
        radar_chart_data={
            "입법활동": 85.2,
            "표결참여": 92.1,
            "회의활동": 68.7,
            "국정감사": 45.3,
            "정책활동": 72.8,
        },
    )

    # 6. 전체 데이터 컨테이너
    member_data = MemberAnalysisData(
        member_name="홍길동",
        raw_bills=[raw_bill],
        raw_member_info=raw_member,
        raw_voting_by_bill=[raw_voting],
        legislative_metrics=legislative_metrics,
        performance_view=performance_view,
    )

    # 7. 데이터 활용
    print("=== 데이터 요약 ===")
    print(f"의원명: {member_data.member_name}")
    print(f"데이터 요약: {member_data.get_data_summary()}")
    print(f"분석 완료 여부: {member_data.is_analysis_complete()}")

    if member_data.raw_member_info:
        print(f"소속 정당: {member_data.raw_member_info.PLPT_NM}")
        print(f"지역구: {member_data.raw_member_info.ELECD_NM}")
        print(f"소속 위원회: {member_data.raw_member_info.BLNG_CMIT_NM}")

    if member_data.performance_view:
        print(f"종합 점수: {member_data.performance_view.overall_score}")
        print(f"성과 등급: {member_data.performance_view.performance_grade}")
        print(f"주요 전문분야: {member_data.performance_view.primary_specialization}")

    # 8. 실제 API 필드 활용 예시
    if member_data.raw_bills:
        bill = member_data.raw_bills[0]
        print(f"\n=== 법안 정보 ===")
        print(f"의안ID: {bill.BILL_ID}")
        print(f"의안명: {bill.BILL_NAME}")
        print(f"제안자: {bill.PROPOSER}")
        print(f"대표발의자: {bill.RST_PROPOSER}")
        print(f"제안일: {bill.PROPOSE_DT}")
        print(f"소관위원회: {bill.COMMITTEE}")
        print(f"본회의 결과: {bill.PROC_RESULT}")
        print(f"상세링크: {bill.DETAIL_LINK}")

    # 9. JSON 저장
    with open(f"{member_data.member_name}_analysis.json", "w", encoding="utf-8") as f:
        json.dump(member_data.to_dict(), f, ensure_ascii=False, indent=2)

    print("\n✅ 분석 데이터가 JSON 파일로 저장되었습니다.")
    print("📋 실제 국회 API 필드명을 사용하여 데이터 구조가 완성되었습니다!")
