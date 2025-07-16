import asyncio
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Union

import aiofiles
import pandas as pd
import pdfplumber

from ...utils.file.fileio import read_file

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BillInfo:
    """법안 기본 정보 구조체"""

    title: str
    bill_number: str
    proposal_date: str
    main_content: str
    reason: str


@dataclass
class AnalysisResult:
    """분석 결과 구조체"""

    bill_info: BillInfo
    policy_field: str
    sub_policy_fields: List[str]
    beneficiary_groups: List[str]
    economic_layers: List[str]
    political_spectrum: Dict[str, float]
    policy_approach: str
    political_implications: List[str]
    ideology_score: float
    urgency_level: str
    social_impact: str


class PoliticalBillAnalyzer:
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)

        # 22대 국회 특성 반영한 정책 분야 (확장 및 최적화)
        self.policy_fields = {
            "디지털정책": [
                "AI",
                "인공지능",
                "빅데이터",
                "디지털",
                "온라인",
                "플랫폼",
                "메타버스",
                "블록체인",
                "가상현실",
                "증강현실",
                "사이버보안",
                "디지털전환",
                "스마트시티",
                "핀테크",
                "디지털정부",
                "전자정부",
                "데이터경제",
                "5G",
                "6G",
                "클라우드",
                "디지털뉴딜",
                "디지털격차",
                "디지털리터러시",
                "사물인터넷",
                "IoT",
            ],
            "경제정책": [
                "경제",
                "산업",
                "투자",
                "기업",
                "세제",
                "지원",
                "육성",
                "금융",
                "자본",
                "시장",
                "경쟁",
                "독점",
                "공정거래",
                "소상공인",
                "자영업",
                "창업",
                "벤처",
                "스타트업",
                "중소기업",
                "중견기업",
                "대기업",
                "재정",
                "예산",
                "기금",
                "경제성장",
                "생산성",
                "효율성",
                "혁신",
                "규제개혁",
                "규제샌드박스",
            ],
            "사회정책": [
                "복지",
                "보장",
                "지원",
                "혜택",
                "보호",
                "배려",
                "사회보험",
                "국민연금",
                "건강보험",
                "고용보험",
                "산재보험",
                "기초생활보장",
                "아동",
                "육아",
                "보육",
                "돌봄",
                "장애인",
                "노인",
                "여성",
                "한부모",
                "다문화",
                "이민",
                "사회안전망",
                "사회통합",
                "소득재분배",
                "불평등",
                "취약계층",
                "소외계층",
            ],
            "지역개발": [
                "지역",
                "개발",
                "균형",
                "낙후",
                "활성화",
                "재생",
                "도시재생",
                "농촌개발",
                "지방분권",
                "지방자치",
                "수도권",
                "비수도권",
                "특별자치",
                "자유경제구역",
                "경제자유구역",
                "지역특화",
                "지역혁신",
                "균형발전",
                "상생협력",
                "지역경제",
                "지역산업",
                "지역일자리",
                "지역문화",
                "관광",
                "축제",
            ],
            "주택정책": [
                "주택",
                "부동산",
                "재개발",
                "재건축",
                "주거",
                "임대",
                "분양",
                "전세",
                "월세",
                "공공임대",
                "사회주택",
                "청년주택",
                "신혼부부",
                "다자녀",
                "주택공급",
                "주택시장",
                "부동산시장",
                "주택가격",
                "전월세",
                "갭투자",
                "부동산투기",
                "투기방지",
                "주택담보대출",
                "주거복지",
                "주거권",
                "주택정책",
                "토지정책",
                "도시계획",
                "용적률",
                "건폐율",
            ],
            "기술혁신": [
                "기술",
                "혁신",
                "첨단",
                "국가전략기술",
                "미래",
                "4차산업",
                "반도체",
                "바이오",
                "헬스케어",
                "의료기기",
                "신약",
                "백신",
                "줄기세포",
                "나노기술",
                "신소재",
                "우주항공",
                "드론",
                "자율주행",
                "전기차",
                "수소차",
                "배터리",
                "태양광",
                "풍력",
                "신재생에너지",
                "원자력",
                "핵융합",
                "양자기술",
                "로봇",
                "3D프린팅",
                "센서",
                "반도체장비",
            ],
            "환경정책": [
                "환경",
                "친환경",
                "에너지",
                "탄소",
                "지속가능",
                "기후변화",
                "온실가스",
                "탄소중립",
                "그린뉴딜",
                "녹색성장",
                "신재생에너지",
                "재활용",
                "폐기물",
                "미세먼지",
                "대기오염",
                "수질오염",
                "토양오염",
                "소음",
                "진동",
                "생태계",
                "생물다양성",
                "자연보호",
                "국립공원",
                "습지",
                "산림",
                "해양",
                "연안",
                "환경영향평가",
                "환경오염",
                "환경보호",
                "지구온난화",
            ],
            "교육정책": [
                "교육",
                "학교",
                "학생",
                "대학",
                "연구",
                "교사",
                "교원",
                "교육과정",
                "입시",
                "수능",
                "내신",
                "사교육",
                "공교육",
                "유아교육",
                "초등교육",
                "중등교육",
                "고등교육",
                "평생교육",
                "직업교육",
                "특수교육",
                "교육격차",
                "교육불평등",
                "교육복지",
                "교육재정",
                "교육시설",
                "원격교육",
                "온라인교육",
                "에듀테크",
                "교육혁신",
                "학령인구",
                "교육개혁",
                "교육자치",
                "교육과정",
                "교육평가",
                "교육연구",
            ],
            "보건의료": [
                "의료",
                "건강",
                "병원",
                "치료",
                "보건",
                "의사",
                "간호사",
                "약사",
                "의료진",
                "환자",
                "질병",
                "감염병",
                "코로나",
                "팬데믹",
                "방역",
                "백신",
                "치료제",
                "의약품",
                "의료기기",
                "의료서비스",
                "의료접근성",
                "의료격차",
                "의료비",
                "건강보험",
                "국민건강",
                "공중보건",
                "정신건강",
                "자살예방",
                "응급의료",
                "의료인력",
                "의료시설",
                "원격의료",
                "디지털헬스케어",
                "정밀의료",
                "개인맞춤의료",
            ],
            "노동정책": [
                "노동",
                "고용",
                "일자리",
                "근로",
                "임금",
                "최저임금",
                "근로시간",
                "휴가",
                "휴직",
                "출산휴가",
                "육아휴직",
                "근로자",
                "사업주",
                "노동조합",
                "단체협약",
                "산업안전",
                "직업병",
                "산재",
                "고용안정",
                "실업",
                "취업",
                "재취업",
                "직업훈련",
                "직업능력개발",
                "일자리창출",
                "청년일자리",
                "여성일자리",
                "고령자일자리",
                "장애인일자리",
                "플랫폼노동",
                "특수고용",
                "프리랜서",
                "긱이코노미",
                "원격근무",
                "재택근무",
                "유연근무",
                "워라밸",
                "일생활균형",
            ],
            "금융정책": [
                "금융",
                "은행",
                "자금",
                "대출",
                "보험",
                "증권",
                "투자",
                "자본시장",
                "주식",
                "채권",
                "펀드",
                "파생상품",
                "가상자산",
                "암호화폐",
                "디지털자산",
                "중앙은행디지털화폐",
                "CBDC",
                "금융위기",
                "금융안정",
                "금융감독",
                "금융규제",
                "금융혁신",
                "금융포용",
                "서민금융",
                "소상공인금융",
                "정책금융",
                "개발금융",
                "녹색금융",
                "지속가능금융",
                "핀테크",
                "인터넷전문은행",
                "디지털금융",
                "금융소비자보호",
            ],
            "문화정책": [
                "문화",
                "예술",
                "창작",
                "콘텐츠",
                "방송",
                "영화",
                "음악",
                "게임",
                "웹툰",
                "만화",
                "애니메이션",
                "전시",
                "공연",
                "축제",
                "문화재",
                "전통문화",
                "한류",
                "케이팝",
                "문화산업",
                "창조경제",
                "문화예술인",
                "문화시설",
                "도서관",
                "박물관",
                "미술관",
                "문화센터",
                "문화다양성",
                "문화향유",
                "문화접근성",
                "문화격차",
                "문화복지",
                "지역문화",
                "생활문화",
                "문화도시",
                "문화유산",
                "무형문화재",
                "스포츠",
                "체육",
                "올림픽",
                "프로스포츠",
                "생활체육",
                "학교체육",
            ],
            "국방정책": [
                "국방",
                "안보",
                "군사",
                "방위",
                "평화",
                "통일",
                "북한",
                "군대",
                "병역",
                "징병",
                "모병",
                "국방력",
                "군사력",
                "방위산업",
                "군수",
                "국방예산",
                "국방개혁",
                "군구조개편",
                "국방인력",
                "장병",
                "국방과학기술",
                "무기체계",
                "방산수출",
                "군사외교",
                "한미동맹",
                "유엔군사령부",
                "전작권",
                "국방정보",
                "사이버안보",
                "국가보안",
                "테러방지",
                "재해대응",
                "민방위",
                "예비군",
                "향토사단",
            ],
            "외교정책": [
                "외교",
                "국제",
                "통상",
                "무역",
                "협력",
                "조약",
                "협정",
                "외교부",
                "재외국민",
                "해외교민",
                "영사",
                "비자",
                "출입국",
                "관광",
                "국제개발협력",
                "ODA",
                "국제기구",
                "유엔",
                "다자외교",
                "양자외교",
                "경제외교",
                "문화외교",
                "공공외교",
                "국제교류",
                "한반도평화",
                "동북아시아",
                "아세안",
                "신남방정책",
                "신북방정책",
                "중견국외교",
                "국제법",
                "국제분쟁",
                "국제중재",
                "국제제재",
            ],
            "농업정책": [
                "농업",
                "농촌",
                "농민",
                "농가",
                "농산물",
                "축산",
                "수산업",
                "임업",
                "농지",
                "농업기술",
                "스마트농업",
                "농업혁신",
                "농촌개발",
                "농업소득",
                "농업경영",
                "농업정책",
                "농업직불금",
                "농업보조금",
                "쌀",
                "밭작물",
                "원예",
                "축산업",
                "낙농",
                "양계",
                "양돈",
                "수산물",
                "어업",
                "어촌",
                "어민",
                "해양수산",
                "양식업",
                "산림",
                "임업",
                "산촌",
                "목재",
                "임산물",
                "산림보호",
                "농촌관광",
                "귀농귀촌",
                "청년농업인",
                "여성농업인",
            ],
            "교통정책": [
                "교통",
                "운송",
                "물류",
                "도로",
                "철도",
                "항공",
                "항만",
                "공항",
                "지하철",
                "버스",
                "택시",
                "자동차",
                "선박",
                "항공기",
                "교통안전",
                "교통사고",
                "교통혼잡",
                "교통체증",
                "대중교통",
                "친환경교통",
                "교통복지",
                "교통인프라",
                "스마트교통",
                "자율주행",
                "전기차",
                "수소차",
                "친환경차",
                "모빌리티",
                "공유교통",
                "카셰어링",
                "킥보드",
                "자전거",
                "보행",
                "교통약자",
                "고속도로",
                "국도",
                "지방도",
                "KTX",
                "고속철도",
                "광역철도",
            ],
        }

        # 22대 국회 특성 반영한 수혜층 패턴 (확장 및 최적화)
        self.beneficiary_patterns = {
            "저소득층": ["저소득", "소득 하위", "서민", "기초생활", "생계급여", "의료급여", "주거급여", "교육급여"],
            "중산층": ["중산층", "일반 가정", "중간소득", "근로자", "샐러리맨", "직장인"],
            "고소득층": ["고소득", "소득 상위", "자산가", "부유층", "고액자산가"],
            "중소기업": ["중소기업", "소기업", "중소상인", "소상공인", "자영업", "개인사업자"],
            "중견기업": ["중견기업", "중간 기업", "중규모"],
            "대기업": ["대기업", "대규모 기업", "대법인", "재벌", "대기업집단"],
            "스타트업": ["스타트업", "창업", "벤처기업", "신생기업", "혁신기업"],
            "플랫폼기업": ["플랫폼", "빅테크", "네이버", "카카오", "쿠팡", "배달의민족", "우버", "그랩"],
            "제조업": ["제조업", "생산", "공장", "산업단지", "제조기업"],
            "서비스업": ["서비스업", "음식점", "카페", "숙박", "미용", "세탁", "수리"],
            "농민": ["농민", "농업", "농촌", "농가", "농업인", "축산업", "수산업", "임업"],
            "노인": ["노인", "고령", "연금", "경로", "실버", "65세", "60세", "시니어"],
            "청년": ["청년", "젊은", "신규 취업", "20대", "30대", "청년층", "밀레니얼"],
            "중장년": ["중장년", "40대", "50대", "중년", "장년층", "베이비부머"],
            "아동": ["아동", "어린이", "유아", "영유아", "초등학생", "미성년자"],
            "학생": ["학생", "대학생", "고등학생", "중학생", "초등학생", "대학원생"],
            "장애인": ["장애인", "장애", "보조기구", "장애우", "중증장애", "경증장애"],
            "여성": ["여성", "모성", "출산", "육아", "여성가족", "한부모", "임산부"],
            "남성": ["남성", "부성", "아버지", "가장", "남성가족"],
            "다문화가족": ["다문화", "이민", "외국인", "국제결혼", "다문화가정", "외국인근로자"],
            "북한이탈주민": ["북한이탈주민", "탈북자", "새터민", "북한출신"],
            "지역주민": ["지역", "거주자", "주민", "지방", "시민", "도민", "군민"],
            "수도권주민": ["수도권", "서울", "경기", "인천", "대도시"],
            "비수도권주민": ["비수도권", "지방", "농촌", "중소도시", "읍면"],
            "전문직": ["전문직", "의사", "변호사", "세무사", "회계사", "건축사", "약사"],
            "예술인": ["예술인", "문화예술인", "창작자", "아티스트", "작가", "음악가", "배우"],
            "프리랜서": ["프리랜서", "특수고용", "플랫폼노동자", "배달기사", "대리기사", "1인 기업"],
            "공무원": ["공무원", "공직자", "교사", "교원", "경찰", "소방관", "군인"],
            "근로자": ["근로자", "노동자", "임금근로자", "사업장", "직장", "회사원"],
            "소비자": ["소비자", "이용자", "구매자", "고객", "이용자"],
            "환자": ["환자", "의료이용자", "치료", "진료", "의료서비스"],
            "임차인": ["임차인", "세입자", "전세", "월세", "임대"],
            "임대인": ["임대인", "집주인", "건물주", "부동산소유자"],
            "택시기사": ["택시기사", "운전기사", "운송업"],
            "배달기사": ["배달기사", "라이더", "배달원"],
            "일반 국민": ["국민", "모든 국민", "일반인", "전체", "전국민"],
        }

        # 22대 국회 특성 반영한 정치적 스펙트럼 키워드 (확장 및 최적화)
        self.political_spectrum_keywords = {
            "진보": {
                "경제": [
                    "복지",
                    "재분배",
                    "공공",
                    "사회적",
                    "형평성",
                    "균형",
                    "불평등해소",
                    "최저임금인상",
                    "기본소득",
                    "전국민고용보험",
                    "사회안전망",
                    "공정경제",
                    "재벌개혁",
                    "소득주도성장",
                    "포용경제",
                    "상생협력",
                    "사회적경제",
                    "협동조합",
                    "사회적기업",
                    "공공금융",
                    "서민금융",
                    "소상공인지원",
                    "골목상권보호",
                    "임금격차해소",
                    "노동존중",
                    "노동자권익",
                    "노동시간단축",
                    "일자리나누기",
                    "공공일자리",
                ],
                "사회": [
                    "인권",
                    "다양성",
                    "포용",
                    "평등",
                    "자유",
                    "개방",
                    "성평등",
                    "차별금지",
                    "소수자보호",
                    "다문화",
                    "이민자권리",
                    "난민",
                    "성소수자",
                    "LGBT",
                    "여성권익",
                    "아동권리",
                    "장애인권리",
                    "노인복지",
                    "청년복지",
                    "사회통합",
                    "문화다양성",
                    "종교의자유",
                    "표현의자유",
                    "언론의자유",
                    "집회결사의자유",
                    "시민사회",
                    "시민참여",
                    "풀뿌리민주주의",
                    "주민자치",
                    "생활정치",
                ],
                "정치": [
                    "개혁",
                    "혁신",
                    "변화",
                    "투명",
                    "참여",
                    "민주",
                    "민주주의",
                    "정치개혁",
                    "선거제도개혁",
                    "국정감사",
                    "정보공개",
                    "권력분산",
                    "지방분권",
                    "자치분권",
                    "주민참여",
                    "시민참여",
                    "열린정부",
                    "정부혁신",
                    "공직윤리",
                    "부패척결",
                    "특권폐지",
                    "기득권개혁",
                    "사법개혁",
                    "검찰개혁",
                    "언론개혁",
                    "교육개혁",
                    "헌법개헌",
                ],
                "환경": [
                    "탄소중립",
                    "그린뉴딜",
                    "친환경",
                    "지속가능",
                    "생태",
                    "기후위기",
                    "신재생에너지",
                    "에너지전환",
                    "탈핵",
                    "원전축소",
                    "환경정의",
                    "환경권",
                    "미세먼지",
                    "대기질",
                    "환경보호",
                    "생태계보전",
                    "녹색교통",
                    "전기차",
                    "수소차",
                    "친환경건축",
                    "녹색건축",
                ],
            },
            "보수": {
                "경제": [
                    "자유시장",
                    "민영화",
                    "효율성",
                    "성장",
                    "기업",
                    "경쟁",
                    "시장경제",
                    "경제성장",
                    "생산성",
                    "경쟁력",
                    "글로벌",
                    "국제경쟁력",
                    "기업활동",
                    "투자유치",
                    "외국인투자",
                    "수출",
                    "무역",
                    "규제완화",
                    "규제개혁",
                    "창업지원",
                    "벤처생태계",
                    "혁신성장",
                    "신성장동력",
                    "4차산업혁명",
                    "첨단기술",
                    "국가전략기술",
                    "반도체",
                    "바이오",
                    "미래차",
                    "신산업",
                    "산업경쟁력",
                    "기업가정신",
                    "자립",
                    "자조",
                    "개인책임",
                    "자유경쟁",
                ],
                "사회": [
                    "전통",
                    "안정",
                    "질서",
                    "보안",
                    "규범",
                    "가족",
                    "전통가족",
                    "가족가치",
                    "전통문화",
                    "국가정체성",
                    "애국",
                    "국가안보",
                    "사회안전",
                    "범죄예방",
                    "치안",
                    "공공안전",
                    "사회질서",
                    "도덕",
                    "윤리",
                    "예의",
                    "예절",
                    "효",
                    "충",
                    "정",
                    "한국적",
                    "민족정신",
                    "전통계승",
                    "문화보존",
                    "역사의식",
                    "국가의식",
                    "개인주의",
                    "자유의지",
                    "자기결정",
                    "개인책임",
                    "성실",
                    "근면",
                    "절약",
                    "저축",
                    "자수성가",
                ],
                "정치": [
                    "안정",
                    "보수",
                    "기존",
                    "유지",
                    "점진적",
                    "실용",
                    "현실",
                    "정치안정",
                    "사회안정",
                    "국가안정",
                    "제도안정",
                    "법질서",
                    "헌법질서",
                    "국가체제",
                    "자유민주주의",
                    "자유민주",
                    "시장민주주의",
                    "법치주의",
                    "삼권분립",
                    "견제균형",
                    "국가권위",
                    "정부권한",
                    "행정효율",
                    "정책연속성",
                    "점진개혁",
                    "실용주의",
                    "현실주의",
                    "안보우선",
                    "경제우선",
                    "성장우선",
                    "효율우선",
                    "국익우선",
                    "실리외교",
                ],
                "안보": [
                    "국방",
                    "안보",
                    "방위",
                    "군사력",
                    "국방력",
                    "억지력",
                    "한미동맹",
                    "동맹강화",
                    "집단안보",
                    "자주국방",
                    "국가보안",
                    "안보위기",
                    "북핵",
                    "북한위협",
                    "중국견제",
                    "사이버안보",
                    "테러방지",
                    "국가기밀",
                    "보안",
                    "첩보",
                    "국정원",
                    "군사정보",
                    "방산",
                    "국방산업",
                    "무기수출",
                ],
            },
        }

        # 긴급성 수준 키워드
        self.urgency_keywords = {
            "매우 긴급": ["긴급", "응급", "즉시", "시급", "조속", "신속", "위기", "재해", "재난"],
            "긴급": ["신속", "빠른", "조기", "우선", "중요", "필요", "요구"],
            "보통": ["점진적", "단계적", "계획적", "체계적", "안정적"],
            "장기": ["장기", "중장기", "지속", "항구적", "항시"],
        }

        # 사회적 영향 키워드
        self.social_impact_keywords = {
            "광범위": ["전국민", "모든", "전체", "광범위", "대규모", "전면적"],
            "상당함": ["상당", "중요", "주요", "핵심", "필수"],
            "제한적": ["특정", "일부", "해당", "관련", "제한"],
            "미미": ["보완", "개선", "정비", "조정", "수정"],
        }

    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """비동기 PDF 텍스트 추출"""

        def _extract_sync(path):
            try:
                with pdfplumber.open(path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                    return text
            except Exception as e:
                logger.error(f"PDF 텍스트 추출 오류 ({path}): {e}")
                return ""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _extract_sync, pdf_path)

    def parse_bill_info(self, text: str) -> BillInfo:
        """법안 기본 정보 파싱 (개선된 정규식)"""
        # 법안 제목 추출 (더 정확한 패턴)
        title_patterns = [
            r"([가-힣\s]+법(?:\s*일부)?개정법률안)",
            r"([가-힣\s]+특별법(?:\s*일부)?개정법률안)",
            r"([가-힣\s]+법률안)",
            r"([가-힣\s]+특별법안)",
        ]

        title = "제목 미확인"
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                break

        # 의안 번호 추출 (다양한 패턴)
        bill_num_patterns = [
            r"의\s*안\s*번\s*호\s*(\d+)",
            r"번\s*호\s*(\d+)",
            r"의안번호\s*(?:제\s*)?(\d+)호",
            r"안\s*번호\s*(\d+)",
        ]

        bill_number = "번호 미확인"
        for pattern in bill_num_patterns:
            match = re.search(pattern, text)
            if match:
                bill_number = match.group(1)
                break

        # 발의자 추출 (더 정확한 패턴)
        proposer_patterns = [
            r"([가-힣]+)\s*의원\s*대표발의",
            r"([가-힣]+)\s*의원이\s*대표발의",
            r"대표발의자?\s*:\s*([가-힣]+)",
            r"발의자\s*:\s*([가-힣]+)",
        ]

        proposer = "발의자 미확인"
        for pattern in proposer_patterns:
            match = re.search(pattern, text)
            if match:
                proposer = match.group(1).strip()
                break

        # 공동발의자 추출 (개선된 패턴)
        co_proposers = []
        co_proposer_patterns = [
            r"발\s*의\s*자\s*:\s*([가-힣\s․·ㆍ]+)\s*(?:의원\s*)?(?:\((\d+)인\))?",
            r"공동발의자?\s*:\s*([가-힣\s․·ㆍ]+)",
            r"([가-힣]+(?:\s*․\s*[가-힣]+)*)\s*의원\s*(?:\((\d+)인\))?",
        ]

        for pattern in co_proposer_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                co_proposer_text = match.group(1)
                # 여러 구분자로 분리
                names = re.split(r"[․·ㆍ\s]+", co_proposer_text)
                co_proposers = [name.strip() for name in names if name.strip() and len(name.strip()) > 1]
                break

        # 발의일자 추출
        date_patterns = [
            r"발의연월일\s*:\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})",
            r"발의일\s*:\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})",
            r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})",
        ]

        proposal_date = "날짜 미확인"
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:
                    proposal_date = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
                else:
                    proposal_date = match.group(1)
                break

        # 제안이유 및 주요내용 추출
        reason_patterns = [
            r"제안이유\s*(?:및\s*주요내용)?\s*[\n\r]*(.*?)(?=법률\s*제|부\s*칙|현\s*행|개\s*정\s*안|$)",
            r"주요내용\s*[\n\r]*(.*?)(?=법률\s*제|부\s*칙|현\s*행|개\s*정\s*안|$)",
            r"제안이유\s*[\n\r]*(.*?)(?=법률\s*제|부\s*칙|현\s*행|개\s*정\s*안|$)",
        ]

        reason = "이유 미확인"
        for pattern in reason_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                reason = match.group(1).strip()
                break

        return BillInfo(
            title=title,
            bill_number=bill_number,
            proposal_date=proposal_date,
            main_content=text,
            reason=reason,
        )

    def classify_policy_field(self, text: str, title_text: str, reason_text: str) -> tuple[str, List[str]]:
        """정책 분야 분류 (주 분야 + 부분야)"""
        field_scores = {}

        # 가중치 적용 (제목과 이유에 더 높은 가중치)
        title_weight = 3.0
        reason_weight = 2.0
        content_weight = 1.0

        for field, keywords in self.policy_fields.items():
            score = 0
            for keyword in keywords:
                # 제목에서 키워드 검색
                score += len(re.findall(keyword, title_text, re.IGNORECASE)) * title_weight
                # 이유에서 키워드 검색
                score += len(re.findall(keyword, reason_text, re.IGNORECASE)) * reason_weight
                # 전체 내용에서 키워드 검색
                score += len(re.findall(keyword, text, re.IGNORECASE)) * content_weight

            field_scores[field] = score

        # 주 분야 결정
        main_field = max(field_scores, key=field_scores.get) if field_scores else "기타"

        # 부분야 결정 (점수가 높은 상위 3개)
        sorted_fields = sorted(field_scores.items(), key=lambda x: x[1], reverse=True)
        sub_fields = [field for field, score in sorted_fields[:3] if score > 0 and field != main_field]

        return main_field, sub_fields

    def analyze_beneficiaries(self, text: str) -> tuple[List[str], List[str]]:
        """수혜층 분석 (개선된 알고리즘)"""
        beneficiary_groups = []
        economic_layers = []

        # 가중치 적용 분석
        for group, patterns in self.beneficiary_patterns.items():
            group_score = 0
            for pattern in patterns:
                # 정확한 매칭에 더 높은 점수
                exact_matches = len(re.findall(f"\\b{pattern}\\b", text, re.IGNORECASE))
                partial_matches = len(re.findall(pattern, text, re.IGNORECASE)) - exact_matches

                group_score += exact_matches * 2 + partial_matches

            if group_score > 0:
                beneficiary_groups.append((group, group_score))

        # 점수 기준으로 정렬하고 상위 결과만 선택
        beneficiary_groups.sort(key=lambda x: x[1], reverse=True)
        beneficiary_groups = [group for group, score in beneficiary_groups[:10]]

        # 경제적 계층 분류 (더 정확한 분류)
        economic_mapping = {
            "서민층": ["저소득층", "농민", "소상공인", "자영업", "근로자", "프리랜서", "배달기사", "택시기사"],
            "중산층": ["중산층", "일반 국민", "공무원", "전문직", "직장인"],
            "고소득층": ["고소득층", "자산가"],
            "기업층": ["중소기업", "중견기업", "대기업", "스타트업", "플랫폼기업", "제조업", "서비스업"],
        }

        for layer, groups in economic_mapping.items():
            if any(group in beneficiary_groups for group in groups):
                economic_layers.append(layer)

        return beneficiary_groups, economic_layers

    def analyze_political_spectrum(self, text: str) -> Dict[str, float]:
        """정치적 이념 스펙트럼 분석 (개선된 알고리즘)"""
        progressive_score = 0
        conservative_score = 0

        # 가중치 적용 분석
        for category, keywords in self.political_spectrum_keywords["진보"].items():
            category_weight = 1.5 if category in ["경제", "사회"] else 1.0
            for keyword in keywords:
                matches = len(re.findall(keyword, text, re.IGNORECASE))
                progressive_score += matches * category_weight

        for category, keywords in self.political_spectrum_keywords["보수"].items():
            category_weight = 1.5 if category in ["경제", "안보"] else 1.0
            for keyword in keywords:
                matches = len(re.findall(keyword, text, re.IGNORECASE))
                conservative_score += matches * category_weight

        total_score = progressive_score + conservative_score
        if total_score == 0:
            return {"진보": 0.5, "보수": 0.5, "중도": 1.0}

        prog_ratio = progressive_score / total_score
        cons_ratio = conservative_score / total_score

        # 중도 성향 계산 (양극화 정도의 역수)
        polarization = abs(prog_ratio - cons_ratio)
        moderate_ratio = 1 - polarization

        return {"진보": prog_ratio, "보수": cons_ratio, "중도": moderate_ratio}

    def analyze_policy_approach(self, text: str) -> str:
        """정책 방식 분석 (더 정확한 분석)"""
        approach_patterns = {
            "새로운 제도 신설": ["신설", "새로", "새롭게", "도입", "창설", "제정"],
            "기존 제도 연장": ["연장", "일몰", "기한", "연기", "유예", "유지"],
            "기존 제도 확대": ["확대", "확장", "늘려", "증가", "증대", "강화"],
            "기존 제도 개정": ["개정", "수정", "변경", "보완", "개선", "정비"],
            "기존 제도 폐지": ["폐지", "삭제", "없애", "철폐", "중단", "종료"],
            "기존 제도 완화": ["완화", "완충", "경감", "축소", "감축", "감소"],
        }

        approach_scores = {}
        for approach, patterns in approach_patterns.items():
            score = 0
            for pattern in patterns:
                score += len(re.findall(pattern, text, re.IGNORECASE))
            approach_scores[approach] = score

        if approach_scores:
            return max(approach_scores, key=approach_scores.get)
        return "기타"

    def analyze_urgency_level(self, text: str) -> str:
        """긴급성 수준 분석"""
        urgency_scores = {}

        for level, keywords in self.urgency_keywords.items():
            score = 0
            for keyword in keywords:
                score += len(re.findall(keyword, text, re.IGNORECASE))
            urgency_scores[level] = score

        if urgency_scores:
            return max(urgency_scores, key=urgency_scores.get)
        return "보통"

    def analyze_social_impact(self, text: str) -> str:
        """사회적 영향 분석"""
        impact_scores = {}

        for impact, keywords in self.social_impact_keywords.items():
            score = 0
            for keyword in keywords:
                score += len(re.findall(keyword, text, re.IGNORECASE))
            impact_scores[impact] = score

        if impact_scores:
            return max(impact_scores, key=impact_scores.get)
        return "보통"

    def derive_political_implications(self, analysis_result: AnalysisResult) -> List[str]:
        """정치적 함의 도출 (확장된 분석)"""
        implications = []

        # 정책 분야별 함의
        field_implications = {
            "디지털정책": "디지털 전환과 4차 산업혁명 대응",
            "지역개발": "지역 균형발전과 분권화 정책",
            "경제정책": "경제성장과 산업 경쟁력 강화",
            "사회정책": "사회적 형평성과 복지 확대",
            "기술혁신": "미래 성장 동력과 혁신 생태계 구축",
            "환경정책": "지속가능한 발전과 기후변화 대응",
            "주택정책": "주거 안정과 부동산 시장 조절",
            "교육정책": "교육 격차 해소와 인재 양성",
            "보건의료": "의료 접근성과 공공보건 강화",
            "노동정책": "노동자 권익 보호와 고용 안정",
            "금융정책": "금융 안정과 서민 금융 지원",
            "문화정책": "문화 향유권과 창조경제 활성화",
            "국방정책": "국가 안보와 방위력 강화",
            "외교정책": "국제 협력과 국익 증진",
            "농업정책": "농업 경쟁력과 농촌 발전",
            "교통정책": "교통 인프라와 이동권 보장",
        }

        if analysis_result.policy_field in field_implications:
            implications.append(field_implications[analysis_result.policy_field])

        # 수혜층별 함의
        if "서민층" in analysis_result.economic_layers:
            implications.append("서민 생활 안정과 소득 재분배")
        if "기업층" in analysis_result.economic_layers:
            implications.append("기업 활동 지원과 투자 촉진")
        if "중산층" in analysis_result.economic_layers:
            implications.append("중산층 보호와 안정적 성장")
        if "고소득층" in analysis_result.economic_layers:
            implications.append("고소득층 대상 정책 조정")

        # 정치적 스펙트럼별 함의
        if analysis_result.political_spectrum["진보"] > 0.6:
            implications.append("진보적 가치 추구와 사회 개혁")
        elif analysis_result.political_spectrum["보수"] > 0.6:
            implications.append("안정성 중시와 기존 질서 유지")
        else:
            implications.append("실용적 정책 접근과 중도 지향")

        # 긴급성별 함의
        if analysis_result.urgency_level == "매우 긴급":
            implications.append("즉각적 대응이 필요한 사회 현안")
        elif analysis_result.urgency_level == "긴급":
            implications.append("신속한 정책 대응 필요")
        elif analysis_result.urgency_level == "장기":
            implications.append("장기적 관점의 정책 추진")

        # 사회적 영향별 함의
        if analysis_result.social_impact == "광범위":
            implications.append("전 국민 대상의 포괄적 정책")
        elif analysis_result.social_impact == "상당함":
            implications.append("사회 전반에 상당한 영향")
        elif analysis_result.social_impact == "제한적":
            implications.append("특정 계층 대상의 맞춤형 정책")

        return implications

    async def get_bill_info(self, path) -> BillInfo:
        text = await read_file(path)
        reason = text.get("sections", {}).get("제안이유", "이유 미확인")
        if len(reason) < 10:
            reason = text.get("sections", {}).get("주요내용", "이유 미확인")
        return BillInfo(
            title=text.get("title", "제목 미확인"),
            bill_number=text.get("bill_number", "번호 미확인"),
            proposal_date=text.get("proposal_date", "날짜 미확인"),
            main_content=text.get("full_text", "내용 미확인"),
            reason=reason,
        )

    async def analyze_single_bill(self, pdf_path: str) -> AnalysisResult:
        """단일 법안 분석 (비동기)"""
        async with self.semaphore:
            # PDF 텍스트 추출
            # text = await self.extract_text_from_pdf(pdf_path)
            # if not text:
            #     raise ValueError("PDF 텍스트 추출 실패")
            bill_info = await self.get_bill_info(pdf_path)
            if not bill_info:
                raise ValueError("PDF 텍스트 추출 실패")
            text = bill_info.main_content

            # 법안 정보 파싱
            # bill_info = self.parse_bill_info(text)

            # 각종 분석 수행
            policy_field, sub_policy_fields = self.classify_policy_field(text, bill_info.title, bill_info.reason)
            beneficiary_groups, economic_layers = self.analyze_beneficiaries(text)
            political_spectrum = self.analyze_political_spectrum(text)
            policy_approach = self.analyze_policy_approach(text)
            urgency_level = self.analyze_urgency_level(text)
            social_impact = self.analyze_social_impact(text)

            # 이념 점수 계산 (진보 -1, 보수 +1 스케일)
            ideology_score = political_spectrum["보수"] - political_spectrum["진보"]

            # 분석 결과 생성
            analysis_result = AnalysisResult(
                bill_info=bill_info,
                policy_field=policy_field,
                sub_policy_fields=sub_policy_fields,
                beneficiary_groups=beneficiary_groups,
                economic_layers=economic_layers,
                political_spectrum=political_spectrum,
                policy_approach=policy_approach,
                political_implications=[],
                ideology_score=ideology_score,
                urgency_level=urgency_level,
                social_impact=social_impact,
            )

            # # 정치적 함의 도출
            analysis_result.political_implications = self.derive_political_implications(analysis_result)
            return analysis_result

    async def analyze_multiple_bills(self, pdf_paths: List[str], progress_callback=None) -> List[AnalysisResult]:
        """여러 법안 일괄 분석 (비동기)"""
        results = []
        failed_files = []

        tasks = []
        for i, pdf_path in enumerate(pdf_paths):
            task = asyncio.create_task(self._analyze_with_progress(pdf_path, i, len(pdf_paths), progress_callback))
            tasks.append(task)

        # 모든 작업 완료 대기
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(completed_tasks):
            if isinstance(result, Exception):
                failed_files.append(pdf_paths[i])
                logger.error(f"법안 분석 실패 ({pdf_paths[i]}): {result}")
            else:
                results.append(result)

        if failed_files:
            logger.warning(f"총 {len(failed_files)}개 파일 분석 실패")

        logger.info(f"전체 분석 완료: {len(results)}개 성공, {len(failed_files)}개 실패")
        return results

    async def _analyze_with_progress(self, pdf_path: str, index: int, total: int, progress_callback) -> AnalysisResult:
        """진행률 콜백과 함께 분석"""
        result = await self.analyze_single_bill(pdf_path)

        if progress_callback:
            progress_callback(index + 1, total, pdf_path)

        return result

    async def save_analysis_results(
        self, results: Union[AnalysisResult, List[AnalysisResult]], output_path: str, format_type: str = "json"
    ):
        """분석 결과 저장 (비동기)"""
        if isinstance(results, AnalysisResult):
            results = [results]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "json":
            output_file = f"{output_path}_analysis_{timestamp}.json"
            await self._save_as_json(results, output_file)
        elif format_type == "excel":
            output_file = f"{output_path}_analysis_{timestamp}.xlsx"
            await self._save_as_excel(results, output_file)
        elif format_type == "text":
            output_file = f"{output_path}_analysis_{timestamp}.txt"
            await self._save_as_text(results, output_file)

        logger.info(f"분석 결과 저장 완료: {output_file}")
        return output_file

    async def _save_as_json(self, results: List[AnalysisResult], file_path: str):
        """JSON 형식으로 저장 (비동기)"""
        json_data = []
        for result in results:
            json_data.append(
                {
                    "bill_info": {
                        "title": result.bill_info.title,
                        "bill_number": result.bill_info.bill_number,
                        "proposal_date": result.bill_info.proposal_date,
                        "reason": result.bill_info.reason,
                    },
                    "analysis": {
                        "policy_field": result.policy_field,
                        "sub_policy_fields": result.sub_policy_fields,
                        "beneficiary_groups": result.beneficiary_groups,
                        "economic_layers": result.economic_layers,
                        "political_spectrum": result.political_spectrum,
                        "policy_approach": result.policy_approach,
                        "political_implications": result.political_implications,
                        "ideology_score": result.ideology_score,
                        "urgency_level": result.urgency_level,
                        "social_impact": result.social_impact,
                    },
                }
            )

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(json_data, ensure_ascii=False, indent=2))

    async def _save_as_excel(self, results: List[AnalysisResult], file_path: str):
        """Excel 형식으로 저장 (비동기)"""

        def _create_dataframe():
            data = []
            for result in results:
                data.append(
                    {
                        "법안명": result.bill_info.title,
                        "의안번호": result.bill_info.bill_number,
                        "발의일자": result.bill_info.proposal_date,
                        "주정책분야": result.policy_field,
                        "부정책분야": ", ".join(result.sub_policy_fields),
                        "수혜층": ", ".join(result.beneficiary_groups),
                        "경제계층": ", ".join(result.economic_layers),
                        "정책방식": result.policy_approach,
                        "진보성향": result.political_spectrum["진보"],
                        "보수성향": result.political_spectrum["보수"],
                        "중도성향": result.political_spectrum["중도"],
                        "이념점수": result.ideology_score,
                        "긴급성": result.urgency_level,
                        "사회적영향": result.social_impact,
                        "정치적함의": "; ".join(result.political_implications),
                    }
                )
            return pd.DataFrame(data)

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(self.executor, _create_dataframe)
        await loop.run_in_executor(self.executor, df.to_excel, file_path, False)

    async def _save_as_text(self, results: List[AnalysisResult], file_path: str):
        """텍스트 형식으로 저장 (비동기)"""
        content = []
        for i, result in enumerate(results, 1):
            content.append(f"=== 법안 {i} 분석 결과 ===\n")
            content.append(f"📋 법안 정보\n")
            content.append(f"- 제목: {result.bill_info.title}\n")
            content.append(f"- 의안번호: {result.bill_info.bill_number}\n")
            content.append(f"- 발의일자: {result.bill_info.proposal_date}\n\n")

            content.append(f"🎯 분석 결과\n")
            content.append(f"- 주정책분야: {result.policy_field}\n")
            content.append(f"- 부정책분야: {', '.join(result.sub_policy_fields)}\n")
            content.append(f"- 수혜층: {', '.join(result.beneficiary_groups)}\n")
            content.append(f"- 경제계층: {', '.join(result.economic_layers)}\n")
            content.append(f"- 정책방식: {result.policy_approach}\n")
            content.append(f"- 이념점수: {result.ideology_score:.2f}\n")
            content.append(f"- 긴급성: {result.urgency_level}\n")
            content.append(f"- 사회적영향: {result.social_impact}\n\n")

            content.append(f"🏛️ 정치적 스펙트럼\n")
            for spectrum, score in result.political_spectrum.items():
                content.append(f"- {spectrum}: {score:.2f}\n")

            content.append(f"\n💡 정치적 함의\n")
            for implication in result.political_implications:
                content.append(f"- {implication}\n")

            content.append(f"\n{'='*50}\n\n")

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write("".join(content))

    def close(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)


# 진행률 콜백 함수
def progress_callback(current, total, current_file):
    """진행률 표시 콜백"""
    progress = (current / total) * 100
    print(f"\r진행률: {progress:.1f}% ({current}/{total}) - {os.path.basename(current_file)}", end="", flush=True)
    if current == total:
        print()  # 완료 시 새 줄


# async def main():
#     """메인 실행 함수"""
#     analyzer = PoliticalBillAnalyzer(max_concurrent_tasks=20)

#     try:
#         # 단일 법안 분석 예제
#         print("=== 단일 법안 분석 ===")
#         result = await analyzer.analyze_single_bill("example_bill.pdf")
#         await analyzer.save_analysis_results(result, "single_bill_analysis", "json")
#         await analyzer.save_analysis_results(result, "single_bill_analysis", "excel")
#         print("단일 법안 분석 완료")

#         # 여러 법안 일괄 분석 예제
#         print("\n=== 여러 법안 일괄 분석 ===")
#         pdf_files = [f"bill_{i:03d}.pdf" for i in range(1, 101)]  # 100개 파일 예제

#         start_time = time.time()
#         results = await analyzer.analyze_multiple_bills(pdf_files, progress_callback)
#         end_time = time.time()

#         await analyzer.save_analysis_results(results, "multiple_bills_analysis", "excel")
#         print(f"총 {len(results)}개 법안 분석 완료 (소요시간: {end_time - start_time:.2f}초)")

#     except Exception as e:
#         print(f"분석 실패: {e}")
#     finally:
#         analyzer.close()


# if __name__ == "__main__":
#     asyncio.run(main())
