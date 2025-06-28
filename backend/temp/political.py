import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

# Korean NLP (실제 사용시 konlpy 설치 필요)
try:
    from konlpy.tag import Komoran, Okt

    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("KoNLPy가 설치되지 않음. 기본 텍스트 분석으로 진행합니다.")


class PoliticalIdeology(Enum):
    """정치 이념 분류"""

    VERY_PROGRESSIVE = "매우 진보"
    PROGRESSIVE = "진보"
    MODERATE = "중도"
    CONSERVATIVE = "보수"
    VERY_CONSERVATIVE = "매우 보수"
    UNKNOWN = "분석불가"


class PolicyArea(Enum):
    """정책 분야"""

    ECONOMY = "경제/금융"
    WELFARE = "복지/사회보장"
    EDUCATION = "교육/과학기술"
    ENVIRONMENT = "환경/에너지"
    SECURITY = "국방/안보"
    FOREIGN_AFFAIRS = "외교/통일"
    JUSTICE = "사법/법무"
    ADMINISTRATION = "행정/지방자치"
    CULTURE = "문화/체육"
    HEALTH = "보건/의료"
    AGRICULTURE = "농림/수산"
    LABOR = "노동/고용"
    TRANSPORTATION = "교통/건설"
    COMMUNICATION = "방송/통신"
    WOMEN_FAMILY = "여성/가족"
    OTHER = "기타"


@dataclass
class SpecializationScore:
    """전문성 점수"""

    area: PolicyArea
    bills_count: int = 0
    speeches_count: int = 0
    committee_activity: float = 0.0
    consistency_score: float = 0.0  # 일관성 점수
    depth_score: float = 0.0  # 깊이 점수
    total_score: float = 0.0


@dataclass
class IdeologyIndicator:
    """이념 지표"""

    keyword_score: float = 0.0  # 키워드 기반 점수
    voting_score: float = 0.0  # 표결 패턴 점수
    bill_score: float = 0.0  # 법안 성향 점수
    alliance_score: float = 0.0  # 정치적 연대 점수
    overall_score: float = 0.0  # 종합 점수


@dataclass
class PoliticalProfile:
    """정치적 프로필"""

    member_name: str
    specializations: List[SpecializationScore] = field(default_factory=list)
    main_interests: List[Tuple[str, float]] = field(
        default_factory=list
    )  # (주제, 관심도)
    ideology: PoliticalIdeology = PoliticalIdeology.UNKNOWN
    ideology_scores: IdeologyIndicator = field(default_factory=IdeologyIndicator)
    activity_timeline: Dict[str, Dict] = field(default_factory=dict)
    keyword_trends: Dict[str, List[float]] = field(default_factory=dict)


class PoliticalKeywords:
    """정치 이념별 키워드 사전"""

    def __init__(self):
        self.progressive_keywords = [
            # 경제 진보 키워드
            "소득불평등",
            "최저임금",
            "부의세",
            "대기업규제",
            "재벌개혁",
            "노동권",
            "사회적경제",
            "공정거래",
            "서민경제",
            "청년일자리",
            # 사회 진보 키워드
            "인권",
            "성평등",
            "다문화",
            "소수자",
            "차별금지",
            "성소수자",
            "여성권익",
            "장애인권",
            "시민권",
            "표현의자유",
            # 복지 진보 키워드
            "보편복지",
            "무상교육",
            "무상의료",
            "기본소득",
            "복지확대",
            "사회보장",
            "공공서비스",
            "복지국가",
            # 환경/평화 키워드
            "탈핵",
            "재생에너지",
            "기후변화",
            "환경보호",
            "평화통일",
            "군축",
            "핵무기반대",
            "반전평화",
        ]

        self.conservative_keywords = [
            # 경제 보수 키워드
            "자유시장",
            "규제완화",
            "민영화",
            "기업활동",
            "투자활성화",
            "세금감면",
            "경제성장",
            "시장경제",
            "경쟁력강화",
            # 사회 보수 키워드
            "전통가치",
            "가족제도",
            "국가정체성",
            "애국",
            "전통문화",
            "도덕성",
            "질서",
            "안정",
            # 안보 보수 키워드
            "국가안보",
            "국방력",
            "한미동맹",
            "북한위협",
            "안보우선",
            "국방예산",
            "군사력",
            "대북제재",
            # 법질서 키워드
            "법질서",
            "처벌강화",
            "범죄예방",
            "사회안전",
            "엄벌주의",
        ]

        self.policy_keywords = {
            PolicyArea.ECONOMY: [
                "경제",
                "금융",
                "투자",
                "기업",
                "산업",
                "무역",
                "수출",
                "GDP",
                "성장",
                "고용",
                "일자리",
                "창업",
                "벤처",
                "스타트업",
                "혁신",
            ],
            PolicyArea.WELFARE: [
                "복지",
                "연금",
                "의료보험",
                "기초생활",
                "사회보장",
                "돌봄",
                "아동",
                "노인",
                "장애인",
                "저소득층",
                "취약계층",
            ],
            PolicyArea.EDUCATION: [
                "교육",
                "대학",
                "입시",
                "학생",
                "교사",
                "과학기술",
                "연구개발",
                "R&D",
                "ICT",
                "AI",
                "디지털",
                "혁신",
            ],
            PolicyArea.ENVIRONMENT: [
                "환경",
                "기후",
                "에너지",
                "탄소",
                "친환경",
                "재생에너지",
                "원전",
                "대기",
                "수질",
                "폐기물",
                "녹색",
                "지속가능",
            ],
            PolicyArea.SECURITY: [
                "국방",
                "안보",
                "군사",
                "북한",
                "통일",
                "한미동맹",
                "평화",
                "군인",
                "병역",
                "국가안전",
            ],
            PolicyArea.JUSTICE: [
                "법률",
                "사법",
                "검찰",
                "법원",
                "재판",
                "법제",
                "개정",
                "헌법",
                "형법",
                "민법",
                "절차",
            ],
        }


class TextAnalyzer:
    """텍스트 분석기"""

    def __init__(self):
        self.keywords_db = PoliticalKeywords()
        if KONLPY_AVAILABLE:
            self.tokenizer = Okt()
        else:
            self.tokenizer = None

    def extract_keywords(self, text: str, top_k: int = 20) -> List[Tuple[str, int]]:
        """텍스트에서 주요 키워드 추출"""
        if not text:
            return []

        # 기본 전처리
        text = self._preprocess_text(text)

        if self.tokenizer:
            # KoNLPy 사용
            tokens = self.tokenizer.nouns(text)
            tokens = [token for token in tokens if len(token) > 1]
        else:
            # 기본 토큰화 (공백 기준)
            tokens = text.split()
            tokens = [token for token in tokens if len(token) > 1]

        # 키워드 빈도 계산
        keyword_freq = Counter(tokens)
        return keyword_freq.most_common(top_k)

    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r"<[^>]+>", "", text)

        # 특수문자 제거 (한글, 영문, 숫자만 유지)
        text = re.sub(r"[^\w\s가-힣]", " ", text)

        # 연속된 공백 제거
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def calculate_ideology_score(self, text: str) -> float:
        """텍스트 기반 이념 점수 계산 (-1: 진보, 0: 중도, +1: 보수)"""
        if not text:
            return 0.0

        text_lower = text.lower()

        progressive_count = sum(
            1
            for keyword in self.keywords_db.progressive_keywords
            if keyword in text_lower
        )
        conservative_count = sum(
            1
            for keyword in self.keywords_db.conservative_keywords
            if keyword in text_lower
        )

        total_keywords = progressive_count + conservative_count
        if total_keywords == 0:
            return 0.0

        # -1 ~ +1 범위로 정규화
        score = (conservative_count - progressive_count) / total_keywords
        return score

    def classify_policy_area(self, text: str) -> Dict[PolicyArea, float]:
        """텍스트의 정책 분야 분류"""
        text_lower = text.lower()
        area_scores = {}

        for area, keywords in self.keywords_db.policy_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            area_scores[area] = score

        # 정규화
        total_score = sum(area_scores.values())
        if total_score > 0:
            area_scores = {
                area: score / total_score for area, score in area_scores.items()
            }

        return area_scores


class SpecializationAnalyzer:
    """전문성 분석기"""

    def __init__(self, text_analyzer: TextAnalyzer):
        self.text_analyzer = text_analyzer

    def analyze_bill_specialization(
        self, bills: List[Dict]
    ) -> Dict[PolicyArea, SpecializationScore]:
        """법안 기반 전문성 분석"""
        area_analysis = defaultdict(lambda: SpecializationScore(area=PolicyArea.OTHER))

        # 위원회별 분야 매핑
        committee_mapping = {
            "기획재정": PolicyArea.ECONOMY,
            "교육": PolicyArea.EDUCATION,
            "과학기술정보방송통신": PolicyArea.COMMUNICATION,
            "외교통일": PolicyArea.FOREIGN_AFFAIRS,
            "국방": PolicyArea.SECURITY,
            "행정안전": PolicyArea.ADMINISTRATION,
            "문화체육관광": PolicyArea.CULTURE,
            "농림축산식품해양수산": PolicyArea.AGRICULTURE,
            "산업통상자원": PolicyArea.ECONOMY,
            "보건복지": PolicyArea.WELFARE,
            "환경노동": PolicyArea.ENVIRONMENT,
            "법제사법": PolicyArea.JUSTICE,
            "정무": PolicyArea.ADMINISTRATION,
            "여성가족": PolicyArea.WOMEN_FAMILY,
            "국토교통": PolicyArea.TRANSPORTATION,
        }

        for bill in bills:
            # 위원회 기반 분야 분류
            committee = bill.get("JRCMIT_NM", "")
            area = PolicyArea.OTHER

            for comm_key, mapped_area in committee_mapping.items():
                if comm_key in committee:
                    area = mapped_area
                    break

            # 법안 제목 기반 추가 분석
            bill_title = bill.get("BILL_NM", "") + " " + bill.get("BILL_SUMMARY", "")
            area_scores = self.text_analyzer.classify_policy_area(bill_title)

            # 가장 높은 점수의 분야 선택
            if area_scores:
                max_area = max(area_scores.items(), key=lambda x: x[1])
                if max_area[1] > 0.1:  # 임계값 이상
                    area = max_area[0]

            # 점수 업데이트
            spec_score = area_analysis[area]
            spec_score.area = area
            spec_score.bills_count += 1

            # 법안 통과 여부에 따른 가중치
            if bill.get("RGS_CONF_RSLT") == "가결":
                spec_score.depth_score += 2.0
            elif bill.get("RGS_CONF_RSLT") == "계류":
                spec_score.depth_score += 1.0
            else:
                spec_score.depth_score += 0.5

        # 일관성 점수 계산 (시간별 활동 분포)
        for area, score in area_analysis.items():
            if score.bills_count > 0:
                # 기본 점수 계산
                score.total_score = score.bills_count * 0.4 + score.depth_score * 0.6

                # 일관성 점수 (법안 수가 많을수록 높음)
                score.consistency_score = min(score.bills_count / 10.0, 1.0)

        return dict(area_analysis)

    def analyze_speech_specialization(
        self, speeches: List[Dict]
    ) -> Dict[PolicyArea, float]:
        """발언 기반 전문성 분석"""
        area_speech_counts = defaultdict(int)

        for speech in speeches:
            content = speech.get("SPEAK_CONT", "")
            if not content:
                continue

            area_scores = self.text_analyzer.classify_policy_area(content)

            # 가장 관련성 높은 분야에 점수 부여
            if area_scores:
                max_area = max(area_scores.items(), key=lambda x: x[1])
                if max_area[1] > 0.1:
                    area_speech_counts[max_area[0]] += 1

        # 정규화
        total_speeches = sum(area_speech_counts.values())
        if total_speeches > 0:
            return {
                area: count / total_speeches
                for area, count in area_speech_counts.items()
            }

        return {}

    def calculate_expertise_ranking(
        self,
        bill_analysis: Dict[PolicyArea, SpecializationScore],
        speech_analysis: Dict[PolicyArea, float],
    ) -> List[SpecializationScore]:
        """전문성 순위 계산"""
        # 법안과 발언 분석 결합
        for area, bill_score in bill_analysis.items():
            speech_score = speech_analysis.get(area, 0.0)

            # 종합 점수 계산
            bill_score.speeches_count = int(speech_score * 100)  # 상대적 발언 횟수
            bill_score.total_score = (
                bill_score.total_score * 0.7 + speech_score * 30 * 0.3
            )  # 법안 70%, 발언 30%

        # 점수순 정렬
        ranked_scores = sorted(
            bill_analysis.values(), key=lambda x: x.total_score, reverse=True
        )

        return ranked_scores[:5]  # 상위 5개 분야


class IdeologyAnalyzer:
    """정치 이념 분석기"""

    def __init__(self, text_analyzer: TextAnalyzer):
        self.text_analyzer = text_analyzer

    def analyze_bill_ideology(self, bills: List[Dict]) -> float:
        """법안 기반 이념 분석"""
        ideology_scores = []

        for bill in bills:
            bill_text = bill.get("BILL_NM", "") + " " + bill.get("BILL_SUMMARY", "")
            score = self.text_analyzer.calculate_ideology_score(bill_text)

            # 법안 통과 여부에 따른 가중치
            weight = 1.0
            if bill.get("RGS_CONF_RSLT") == "가결":
                weight = 2.0  # 통과된 법안에 더 높은 가중치

            ideology_scores.extend([score] * int(weight))

        return np.mean(ideology_scores) if ideology_scores else 0.0

    def analyze_speech_ideology(self, speeches: List[Dict]) -> float:
        """발언 기반 이념 분석"""
        ideology_scores = []

        for speech in speeches:
            content = speech.get("SPEAK_CONT", "")
            if content:
                score = self.text_analyzer.calculate_ideology_score(content)
                ideology_scores.append(score)

        return np.mean(ideology_scores) if ideology_scores else 0.0

    def analyze_voting_ideology(
        self, voting_records: List[Dict], party_positions: Dict[str, float] = None
    ) -> float:
        """표결 기반 이념 분석"""
        if not party_positions:
            # 기본 정당별 이념 점수 (-1: 진보, +1: 보수)
            party_positions = {
                "더불어민주당": -0.3,
                "국민의힘": 0.4,
                "정의당": -0.8,
                "국민의당": 0.1,
                "기본소득당": -0.9,
                "시대전환": -0.4,
            }

        ideology_scores = []

        for vote in voting_records:
            vote_result = vote.get("VOTE_RSLT", "")
            bill_id = vote.get("BILL_ID", "")

            # 법안별 정당 표결 패턴 분석 (실제로는 더 복잡한 로직 필요)
            # 여기서는 단순화된 버전
            if vote_result in ["찬성", "반대"]:
                # 소속 정당의 기본 이념 점수 사용
                member_party = vote.get("PARTY_NM", "")
                if member_party in party_positions:
                    ideology_scores.append(party_positions[member_party])

        return np.mean(ideology_scores) if ideology_scores else 0.0

    def classify_ideology(
        self, ideology_indicator: IdeologyIndicator
    ) -> PoliticalIdeology:
        """종합 이념 분류"""
        overall_score = ideology_indicator.overall_score

        if overall_score < -0.6:
            return PoliticalIdeology.VERY_PROGRESSIVE
        elif overall_score < -0.2:
            return PoliticalIdeology.PROGRESSIVE
        elif overall_score < 0.2:
            return PoliticalIdeology.MODERATE
        elif overall_score < 0.6:
            return PoliticalIdeology.CONSERVATIVE
        else:
            return PoliticalIdeology.VERY_CONSERVATIVE


class InterestAnalyzer:
    """관심 분야 분석기"""

    def __init__(self, text_analyzer: TextAnalyzer):
        self.text_analyzer = text_analyzer

    def analyze_temporal_interests(
        self, activities: List[Dict], time_windows: int = 6
    ) -> Dict[str, List[float]]:
        """시간별 관심 변화 분석"""
        # 활동을 시간순 정렬
        sorted_activities = sorted(
            activities, key=lambda x: x.get("date", "2000-01-01")
        )

        if not sorted_activities:
            return {}

        # 시간 구간 나누기
        start_date = datetime.strptime(
            sorted_activities[0].get("date", "2020-01-01"), "%Y-%m-%d"
        )
        end_date = datetime.strptime(
            sorted_activities[-1].get("date", "2024-01-01"), "%Y-%m-%d"
        )

        time_interval = (end_date - start_date) / time_windows
        keyword_timeline = defaultdict(lambda: [0] * time_windows)

        for activity in sorted_activities:
            activity_date = datetime.strptime(
                activity.get("date", "2020-01-01"), "%Y-%m-%d"
            )
            time_index = min(
                int((activity_date - start_date) / time_interval), time_windows - 1
            )

            # 텍스트에서 키워드 추출
            text = activity.get("title", "") + " " + activity.get("content", "")
            keywords = self.text_analyzer.extract_keywords(text, top_k=10)

            for keyword, count in keywords:
                keyword_timeline[keyword][time_index] += count

        return dict(keyword_timeline)

    def identify_core_interests(
        self, all_activities: List[Dict], min_frequency: int = 3
    ) -> List[Tuple[str, float]]:
        """핵심 관심사 식별"""
        all_text = ""
        for activity in all_activities:
            text = activity.get("title", "") + " " + activity.get("content", "")
            all_text += text + " "

        # 전체 키워드 추출
        keywords = self.text_analyzer.extract_keywords(all_text, top_k=50)

        # 최소 빈도 이상인 키워드만 선택
        core_interests = [
            (keyword, freq) for keyword, freq in keywords if freq >= min_frequency
        ]

        # 관심도 점수 계산 (빈도 + 지속성)
        total_freq = sum(freq for _, freq in core_interests)
        normalized_interests = [
            (keyword, freq / total_freq) for keyword, freq in core_interests
        ]

        return normalized_interests[:20]  # 상위 20개


class PoliticalProfiler:
    """통합 정치 프로필 분석기"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.text_analyzer = TextAnalyzer()
        self.specialization_analyzer = SpecializationAnalyzer(self.text_analyzer)
        self.ideology_analyzer = IdeologyAnalyzer(self.text_analyzer)
        self.interest_analyzer = InterestAnalyzer(self.text_analyzer)

    def create_comprehensive_profile(self, member_name: str) -> PoliticalProfile:
        """종합 정치 프로필 생성"""
        print(f"의원 '{member_name}' 정치 프로필 분석 중...")

        # 기본 데이터 수집
        bills = self.api_client.get_bills_by_member(member_name)
        speeches = self.api_client.get_plenary_minutes(member_name)
        speeches.extend(self.api_client.get_committee_minutes(member_name))
        voting_records = self.api_client.get_voting_records(member_name)

        # 활동 데이터 통합
        all_activities = []

        # 법안 데이터 변환
        for bill in bills:
            all_activities.append(
                {
                    "type": "bill",
                    "date": bill.get("PPSL_DT", "2020-01-01"),
                    "title": bill.get("BILL_NM", ""),
                    "content": bill.get("BILL_SUMMARY", ""),
                }
            )

        # 발언 데이터 변환
        for speech in speeches:
            all_activities.append(
                {
                    "type": "speech",
                    "date": speech.get("MTGDT", "2020-01-01"),
                    "title": f"회의 발언",
                    "content": speech.get("SPEAK_CONT", ""),
                }
            )

        # 1. 전문성 분석
        bill_specialization = self.specialization_analyzer.analyze_bill_specialization(
            bills
        )
        speech_specialization = (
            self.specialization_analyzer.analyze_speech_specialization(speeches)
        )
        specializations = self.specialization_analyzer.calculate_expertise_ranking(
            bill_specialization, speech_specialization
        )

        # 2. 이념 분석
        bill_ideology = self.ideology_analyzer.analyze_bill_ideology(bills)
        speech_ideology = self.ideology_analyzer.analyze_speech_ideology(speeches)
        voting_ideology = self.ideology_analyzer.analyze_voting_ideology(voting_records)

        ideology_indicator = IdeologyIndicator(
            bill_score=bill_ideology,
            keyword_score=speech_ideology,
            voting_score=voting_ideology,
            overall_score=(
                bill_ideology * 0.4 + speech_ideology * 0.3 + voting_ideology * 0.3
            ),
        )

        ideology = self.ideology_analyzer.classify_ideology(ideology_indicator)

        # 3. 관심사 분석
        core_interests = self.interest_analyzer.identify_core_interests(all_activities)
        interest_timeline = self.interest_analyzer.analyze_temporal_interests(
            all_activities
        )

        # 4. 시간별 활동 패턴
        activity_timeline = self._create_activity_timeline(all_activities)

        return PoliticalProfile(
            member_name=member_name,
            specializations=specializations,
            main_interests=core_interests,
            ideology=ideology,
            ideology_scores=ideology_indicator,
            activity_timeline=activity_timeline,
            keyword_trends=interest_timeline,
        )

    def _create_activity_timeline(self, activities: List[Dict]) -> Dict[str, Dict]:
        """활동 타임라인 생성"""
        timeline = defaultdict(lambda: {"bills": 0, "speeches": 0, "total": 0})

        for activity in activities:
            date_str = activity.get("date", "2020-01-01")
            year_month = date_str[:7]  # YYYY-MM 형태

            activity_type = activity.get("type", "other")
            timeline[year_month][activity_type] += 1
            timeline[year_month]["total"] += 1

        return dict(timeline)


class ProfileReporter:
    """프로필 보고서 생성기"""

    @staticmethod
    def generate_comprehensive_report(profile: PoliticalProfile) -> str:
        """종합 프로필 보고서 생성"""
        report = f"""
{'='*80}
국회의원 정치적 프로필 분석 보고서
{'='*80}

👤 의원명: {profile.member_name}

🎯 정치 이념 분석
- 종합 이념: {profile.ideology.value}
- 이념 점수: {profile.ideology_scores.overall_score:.3f} 
  (진보 ← -1.0 ～ 0 ～ +1.0 → 보수)

📊 세부 이념 지표:
- 법안 기반 점수: {profile.ideology_scores.bill_score:.3f}
- 발언 기반 점수: {profile.ideology_scores.keyword_score:.3f}  
- 표결 기반 점수: {profile.ideology_scores.voting_score:.3f}

🏆 전문 분야 (상위 5개)
"""

        for i, spec in enumerate(profile.specializations[:5], 1):
            report += f"""
{i}. {spec.area.value}
   - 관련 법안: {spec.bills_count}건
   - 전문성 점수: {spec.total_score:.1f}점
   - 일관성: {spec.consistency_score:.1f}점
   - 깊이: {spec.depth_score:.1f}점
"""

        report += "\n💡 핵심 관심사 (상위 10개)\n"
        for i, (interest, score) in enumerate(profile.main_interests[:10], 1):
            report += f"{i:2d}. {interest} ({score:.1%})\n"

        # 활동 패턴 요약
        if profile.activity_timeline:
            recent_months = sorted(profile.activity_timeline.keys())[-6:]
            total_recent = sum(
                profile.activity_timeline[month]["total"] for month in recent_months
            )
            avg_monthly = total_recent / len(recent_months) if recent_months else 0

            report += f"""
📈 최근 활동 패턴 (최근 6개월)
- 월평균 활동: {avg_monthly:.1f}건
- 활동 분포: """

            for month in recent_months[-3:]:  # 최근 3개월
                data = profile.activity_timeline[month]
                report += f"\n  {month}: 총 {data['total']}건 (법안 {data.get('bills', 0)}건, 발언 {data.get('speeches', 0)}건)"

        # 이념적 특징 해석
        report += f"\n\n🧭 정치적 특징 해석\n"

        ideology_score = profile.ideology_scores.overall_score
        if ideology_score < -0.3:
            report += (
                "- 진보적 성향을 보이는 의원으로, 사회 개혁과 복지 확대에 관심이 높음\n"
            )
        elif ideology_score > 0.3:
            report += "- 보수적 성향을 보이는 의원으로, 시장 경제와 전통 가치 중시\n"
        else:
            report += "- 중도적 성향을 보이는 의원으로, 실용적이고 합리적인 정책 추진\n"

        # 전문성 특징
        if profile.specializations:
            main_area = profile.specializations[0].area.value
            report += f"- 주요 전문 분야는 '{main_area}'로, 해당 분야에서 지속적인 활동을 보임\n"

        report += f"\n{'='*80}\n"

        return report

    @staticmethod
    def create_visualization_data(profile: PoliticalProfile) -> Dict:
        """시각화용 데이터 생성"""
        # 전문성 차트 데이터
        spec_data = {
            "areas": [spec.area.value for spec in profile.specializations[:5]],
            "scores": [spec.total_score for spec in profile.specializations[:5]],
        }

        # 관심사 워드클라우드 데이터
        interest_data = {word: score for word, score in profile.main_interests[:30]}

        # 이념 점수 레이더 차트 데이터
        ideology_data = {
            "bill_score": profile.ideology_scores.bill_score,
            "speech_score": profile.ideology_scores.keyword_score,
            "voting_score": profile.ideology_scores.voting_score,
            "overall_score": profile.ideology_scores.overall_score,
        }

        # 시간별 활동 추이 데이터
        timeline_data = {
            "months": list(profile.activity_timeline.keys()),
            "activities": [
                data["total"] for data in profile.activity_timeline.values()
            ],
        }

        return {
            "specialization": spec_data,
            "interests": interest_data,
            "ideology": ideology_data,
            "timeline": timeline_data,
        }


# 사용 예시
def main():
    """메인 실행 함수"""
    # API 키 설정
    API_KEY = "YOUR_API_KEY_HERE"

    # API 클라이언트 초기화 (이전 코드의 클라이언트 재사용)
    api_client = NationalAssemblyAPI(API_KEY)

    # 프로파일러 초기화
    profiler = PoliticalProfiler(api_client)

    # 분석할 의원
    member_name = "홍길동"

    try:
        # 종합 프로필 생성
        profile = profiler.create_comprehensive_profile(member_name)

        # 보고서 생성 및 출력
        report = ProfileReporter.generate_comprehensive_report(profile)
        print(report)

        # 시각화 데이터 생성
        viz_data = ProfileReporter.create_visualization_data(profile)

        print("📊 분석 결과 요약:")
        print(
            f"- 주요 전문 분야: {profile.specializations[0].area.value if profile.specializations else '없음'}"
        )
        print(f"- 정치 이념: {profile.ideology.value}")
        print(
            f"- 핵심 관심사: {', '.join([word for word, _ in profile.main_interests[:3]])}"
        )
        print(
            f"- 최근 6개월 활동량: {sum(data['total'] for data in list(profile.activity_timeline.values())[-6:])}건"
        )

        # 프로필 데이터 저장
        with open(f"{member_name}_political_profile.json", "w", encoding="utf-8") as f:
            # 데이터클래스를 딕셔너리로 변환하여 저장
            profile_dict = {
                "member_name": profile.member_name,
                "ideology": profile.ideology.value,
                "ideology_scores": profile.ideology_scores.__dict__,
                "specializations": [spec.__dict__ for spec in profile.specializations],
                "main_interests": profile.main_interests,
                "activity_timeline": profile.activity_timeline,
                "keyword_trends": profile.keyword_trends,
            }
            json.dump(profile_dict, f, ensure_ascii=False, indent=2)

        print(
            f"\n✅ 프로필 분석 완료! 결과가 '{member_name}_political_profile.json'에 저장되었습니다."
        )

    except Exception as e:
        print(f"프로필 분석 중 오류 발생: {e}")


# 비교 분석 함수
def compare_members(api_client, member_names: List[str]):
    """여러 의원 비교 분석"""
    profiler = PoliticalProfiler(api_client)
    profiles = []

    for name in member_names:
        try:
            profile = profiler.create_comprehensive_profile(name)
            profiles.append(profile)
        except Exception as e:
            print(f"의원 '{name}' 분석 실패: {e}")

    # 비교 결과 출력
    print(f"\n{'='*60}")
    print(f"국회의원 비교 분석 ({len(profiles)}명)")
    print(f"{'='*60}")

    print(f"{'의원명':<10} {'이념성향':<15} {'주요분야':<15} {'이념점수':<10}")
    print("-" * 60)

    for profile in profiles:
        main_area = (
            profile.specializations[0].area.value if profile.specializations else "없음"
        )
        ideology_score = profile.ideology_scores.overall_score

        print(
            f"{profile.member_name:<10} {profile.ideology.value:<15} "
            f"{main_area:<15} {ideology_score:>+6.2f}"
        )


if __name__ == "__main__":
    main()
