from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from model import PolicyArea


# ==================== RAW DATA STRUCTURES ====================
@dataclass
class RawMemberData:
    """
    원시 의원 데이터
    https://open.assembly.go.kr/portal/data/service/selectAPIServicePage.do/OOWY4R001216HX11439
    """

    NAAS_CD: str = ""  # 국회의원코드
    NAAS_NM: str = ""  # 국회의원명
    NAAS_CH_NM: str = ""  # 국회의원한자명
    NAAS_EN_NM: str = ""  # 국회의원영문명
    BIRDY_DIV_CD: str = ""  # 생일구분코드
    BIRDY_DT: str = ""  # 생일일자
    DTY_NM: str = ""  # 직책명
    PLPT_NM: str = ""  # 정당명
    ELECD_NM: str = ""  # 선거구명
    ELECD_DIV_NM: str = ""  # 선거구구분명
    CMIT_NM: str = ""  # 위원회명
    BLNG_CMIT_NM: str = ""  # 소속위원회명
    RLCT_DIV_NM: str = ""  # 재선구분명
    GTELT_ERACO: str = ""  # 당선대수
    NTR_DIV: str = ""  # 성별ß
    NAAS_TEL_NO: str = ""  # 전화번호
    NAAS_EMAIL_ADDR: str = ""  # 국회의원이메일주소
    NAAS_HP_URL: str = ""  # 국회의원홈페이지URL
    AIDE_NM: str = ""  # 보좌관
    CHF_SCRT_NM: str = ""  # 비서관
    SCRT_NM: str = ""  # 비서
    BRF_HST: str = ""  # 약력
    OFFM_RNUM_NO: str = ""  # 사무실 호실
    NAAS_PIC: str = ""  # 국회의원 사진

    # 메타데이터
    api_name: str = "ALLNAMEMBER"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/ALLMEMBER"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    required_params = ()
    valid_params = {"NAAS_CD", "NAAS_NAME", "BLNG_CMIT_NM", "PLPT_NM"}


@dataclass
class RawCommittee:
    CMT_DIV_CD: str = ""  # 	위원회구분코드
    CMT_DIV_NM: str = ""  # 	위원회구분
    HR_DEPT_CD: str = ""  # 	위원회코드
    COMMITTEE_NAME: str = ""  # 	위원회
    HG_NM: str = ""  # 	위원장
    HG_NM_LIST: str = ""  # 	간사
    LIMIT_CNT: str = ""  # 	위원정수
    CURR_CNT: str = ""  # 	현원
    POLY99_CNT: str = ""  # 	비교섭단체위원수
    POLY_CNT: str = ""  # 	교섭단체위원수
    ORDER_NUM: str = ""

    # 메타데이터
    api_name: str = "committees"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/nxrvzonlafugpqjuh"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawLawBillMemberData:
    """
    원시 법률안 데이터(국회의원, 공동발의자 리스트 있음. )
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OK7XM1000938DS17215
    필수: AGE = 대수
    """

    BILL_ID: str = ""  # 의안ID
    BILL_NO: str = ""  # 의안번호
    BILL_NAME: str = ""  # 법률안명
    COMMITTEE: str = ""  # 소관위원회
    PROPOSE_DT: str = ""  # 제안일
    PROC_RESULT: str = ""  # 본회의심의결과
    AGE: str = ""  # 대수
    DETAIL_LINK: str = ""  # 상세페이지
    PROPOSER: str = ""  # 제안자
    MEMBER_LIST: str = ""  # 제안자목록링크
    LAW_PROC_DT: str = ""  # 법사위처리일
    LAW_PRESENT_DT: str = ""  # 법사위상정일
    LAW_SUBMIT_DT: str = ""  # 법사위회부일
    CMT_PROC_RESULT_CD: str = ""  # 소관위처리결과
    CMT_PROC_DT: str = ""  # 소관위처리일
    CMT_PRESENT_DT: str = ""  # 소관위상정일
    COMMITTEE_DT: str = ""  # 소관위회부일
    PROC_DT: str = ""  # 의결일
    COMMITTEE_ID: str = ""  # 소관위원회ID
    LAW_PROC_RESULT_CD: str = ""  # 법사위처리결과
    PUBL_PROPOSER: str = ""  # 공동발의자
    RST_PROPOSER: str = ""  # 대표발의자

    # 메타데이터
    api_name: str = "law_bill_member"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawLawBillAllData:
    """
    원시 법률안 데이터(정부, 위원장 발의 포함.)
    https://open.assembly.go.kr/portal/data/service/selectAPIServicePage.do/O4K6HM0012064I15889
    필수: AGE = 대수
    """

    BILL_ID: str = ""  # 의안ID
    BILL_NO: str = ""  # 의안번호
    BILL_NAME: str = ""  # 법률안명
    COMMITTEE: str = ""  # 소관위원회
    PROPOSE_DT: str = ""  # 제안일
    PROC_RESULT: str = ""  # 본회의심의결과
    AGE: str = ""  # 대수
    DETAIL_LINK: str = ""  # 상세페이지
    PROPOSER: str = ""  # 제안자
    MEMBER_LIST: str = ""  # 제안자목록링크
    LAW_PROC_DT: str = ""  # 법사위처리일
    LAW_PRESENT_DT: str = ""  # 법사위상정일
    LAW_SUBMIT_DT: str = ""  # 법사위회부일
    CMT_PROC_RESULT_CD: str = ""  # 소관위처리결과
    CMT_PROC_DT: str = ""  # 소관위처리일
    CMT_PRESENT_DT: str = ""  # 소관위상정일
    COMMITTEE_DT: str = ""  # 소관위회부일
    PROC_DT: str = ""  # 의결일
    COMMITTEE_ID: str = ""  # 소관위원회ID
    LAW_PROC_RESULT_CD: str = ""  # 법사위처리결과
    PUBL_PROPOSER: str = ""  # 공동발의자
    RST_PROPOSER: str = ""  # 대표발의자

    # 메타데이터
    api_name: str = "law_bill_all"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/TVBPMBILL11"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawVotingByBillData:
    """
    원시 의안별 표결 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OND1KZ0009677M13515
    # 본회의 표결 결과
    """

    BILL_ID: str = ""  # 	의안ID
    PROC_DT: str = ""  # 	처리일
    BILL_NO: str = ""  # 	의안번호
    BILL_NAME: str = ""  # 	의안명
    CURR_COMMITTEE: str = ""  # 	소관위
    CURR_COMMITTEE_ID: str = ""  # 	소관위코드
    PROC_RESULT_CD: str = ""  # 	표결결과
    BILL_KIND_CD: str = ""  # 	의안종류
    AGE: str = ""  # 	대수
    MEMBER_TCNT: str = ""  # 	재적의원
    VOTE_TCNT: str = ""  # 	총투표수
    YES_TCNT: str = ""  # 	찬성
    NO_TCNT: str = ""  # 	반대
    BLANK_TCNT: str = ""  # 	기권
    LINK_URL: str = ""  # 	의안상세정보 URL

    # 메타데이터
    api_name: str = "voting_by_bill"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/ncocpgfiaoituanbr"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawPlenaryVotingData:
    """
    원시 본회의 표결 데이터
    """

    HG_NM: str = ""  # 의원
    HJ_NM: str = ""  # 한자명
    POLY_NM: str = ""  # 정당
    ORIG_NM: str = ""  # 선거구
    MEMBER_NO: str = ""  # 의원번호
    POLY_CD: str = ""  # 소속정당코드
    ORIG_CD: str = ""  # 선거구코드
    VOTE_DATE: str = ""  # 의결일자
    BILL_NO: str = ""  # 의안번호
    BILL_NAME: str = ""  # 의안명
    BILL_ID: str = ""  # 의안ID
    LAW_TITLE: str = ""  # 법률명
    CURR_COMMITTEE: str = ""  # 소관위원회
    RESULT_VOTE_MOD: str = ""  # 표결결과
    DEPT_CD: str = ""  # 부서코드(사용안함)
    CURR_COMMITTEE_ID: str = ""  # 소관위코드
    DISP_ORDER: str = ""  # 표시정렬순서
    BILL_URL: str = ""  # 의안URL
    BILL_NAME_URL: str = ""  # 의안링크
    SESSION_CD: str = ""  # 회기
    CURRENTS_CD: str = ""  # 차수
    AGE: str = ""  # 대
    MONA_CD: str = ""  # 국회의원코드

    # 메타데이터
    api_name: str = "plenary_voting"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawPlenaryMinutesData:
    """
    원시 본회의 회의록 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OO1X9P001017YF13038
    """

    CONFER_NUM: str = ""  # 회의번호
    TITLE: str = ""  # 회의명
    CLASS_NAME: str = ""  # 회의종류명
    DAE_NUM: str = ""  # 대수
    CONF_DATE: str = ""  # 회의날짜
    SUB_NAME: str = ""  # 안건명
    VOD_LINK_URL: str = ""  # 영상회의록 링크
    CONF_LINK_URL: str = ""  # 요약정보 팝업
    PDF_LINK_URL: str = ""  # PDF파일 링크

    # 메타데이터
    api_name: str = "plenary_minutes"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/nzbyfwhwaoanttzje"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawCommitteeMinutesData:
    """
    원시 위원회 회의록 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OR137O001023MZ19321
    """

    CONFER_NUM: str = ""  # 회의번호
    TITLE: str = ""  # 회의명
    CLASS_NAME: str = ""  # 회의종류명
    DAE_NUM: str = ""  # 대수
    COMM_NAME: str = ""  # 위원회명
    VODCOMM_CODE: str = ""  # 영상회의록
    CONF_DATE: str = ""  # 회의날짜
    SUB_NAME: str = ""  # 안건명
    VOD_LINK_URL: str = ""  # 영상회의록 링크
    CONF_LINK_URL: str = ""  # 요약정보 팝업
    PDF_LINK_URL: str = ""  # PDF파일 링크
    PDF_FILE_ID: str = ""  # 회의록
    DEPT_CD: str = ""  # 위원회코드

    # 메타데이터
    api_name: str = "committee_minutes"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/ncwgseseafwbuheph"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    required_params = {}
    valid_params = {}


@dataclass
class RawAuditReportData:
    """
    원시 국정감사 결과보고서 데이터
    https://open.assembly.go.kr/portal/data/service/selectAPIServicePage.do/OOWY4R001216HX11497
    """

    RPT_YR: str = ""  # 보고서 년도
    CMIT_NM: str = ""  # 위원회명
    RPT_TTL: str = ""  # 보고서 제목
    PDF_DWLD_URL: str = ""  # PDF 다운 URL
    HWP_DWLD_URL: str = ""  # HWP 다운 URL

    # 메타데이터
    api_name: str = "audit_report"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/AUDITREPORTRESULT"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawSNSData:
    """
    원시 SNS 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OET0D9001078G318850
    """

    HG_NM: str = ""  # 이름
    T_URL: str = ""  # 트위터 URL
    F_URL: str = ""  # 페이스북 URL
    Y_URL: str = ""  # 유튜브 URL
    B_URL: str = ""  # 블로그 URL
    MONA_CD: str = ""  # 국회의원코드

    # 메타데이터
    api_name: str = "sns_activity"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/negnlnyvatsjwocar"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawActivityData:
    """
    원시 국회의원 활동 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OOWY4R001216HX11501
    """

    NAAS_NM: str = "" # 국회의원명	
    EV_TTL: str = "" # 행사 제목  
    EV_DTM: str = "" # 행사 일시  
    EV_PLC: str = "" # 행사 장소  
    LINK_URL: str = "" # 행사 URL

    # 메타데이터
    api_name: str = "activity"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/NAMEMBEREVENT"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawTakingData:
    """
    원시 국회의원 기자회견 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OZY6M30010164K11655
    """

    TAKING_DATE: str = "" # 회견일, 
    OPEN_TIME: str = "" # 회견시각, 
    TITLE: str = "" # 제목, 
    PERSON: str = "" # 발언자, 
    REC_TIME: str = "" # 재생시간, 
    LINK_URL: str = "" # 링크 URL 

    # 메타데이터
    api_name: str = "taking"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/npbzvuwvasdqldskm"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawPromiseData:
    """원시 공약 데이터 (수동 입력)"""

    promise_id: str
    member_name: str
    title: str
    content: str
    category: PolicyArea
    keywords: List[str] = field(default_factory=list)
    target_date: str = ""
    priority: int = 3  # 1(높음) ~ 5(낮음)
    specific_bills: List[str] = field(default_factory=list)  # 구체적 법안명
    measurable: bool = True

    # 메타데이터
    source: str = "manual"  # manual/crawling/api
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawLegislativePreviewData:
    """
    원시 입법예고 데이터
    https://open.assembly.go.kr/portal/data/service/selectServicePage.do?infId=OXJ0OE001002XA11874
    """

    BILL_ID: str = ""  # 의안 ID
    BILL_NO: str = ""  # 의안번호
    BILL_NAME: str = ""  # 법률안명
    AGE: str = ""  # 대
    PROPOSER_KIND_CD: str = ""  # 제안자구분
    CURR_COMMITTEE: str = ""  # 소관위원회
    NOTI_ED_DT: str = ""  # 게시종료일
    LINK_URL: str = ""  # 링크주소
    PROPOSER: str = ""  # 제안자
    CURR_COMMITTEE_ID: str = ""  # 소관위ID

    # 메타데이터
    api_name: str = "legislative_preview"
    source_api: str = "https://open.assembly.go.kr/portal/openapi/nknalejkafmvgzmpt"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RawBillData:
    """
    원시 의안 데이터
    https://open.assembly.go.kr/portal/data/service/selectAPIServicePage.do/OOWY4R001216HX11440
    필수: BILL_NO = 의안번호
    """

    ERACO: str = ""  # 대수
    BILL_ID: str = ""  # 의안ID
    BILL_NO: str = ""  # 의안번호
    BILL_KND: str = ""  # 의안종류
    BILL_NM: str = ""  # 의안명
    PPSR_KND: str = ""  # 제안자구분
    PPSR_NM: str = ""  # 제안자명(등 48인)
    PPSL_SESS: str = ""  # 제안회기
    PPSL_DT: str = ""  # 제안일
    JRCMIT_NM: str = ""  # 소관위원회명
    JRCMIT_CMMT_DT: str = ""  # 소관위원회 회부일
    JRCMIT_PRSNT_DT: str = ""  # 소관위원회 상정일
    JRCMIT_PROC_DT: str = ""  # 소관위원회 처리일
    JRCMIT_PROC_RSLT: str = ""  # 소관위원회 처리결과
    LAW_CMMT_DT: str = ""  # 법사위 체계자구심사 회부일
    LAW_PRSNT_DT: str = ""  # 법사위 체계자구심사 상정일
    LAW_PROC_DT: str = ""  # 법사위 체계자구심사 처리일
    LAW_PROC_RSLT: str = ""  # 법사위 체계자구심사 처리결과
    RGS_PRSNT_DT: str = ""  # 본회의 심의 상정일
    RGS_RSLN_DT: str = ""  # 본회의 심의 의결일
    RGS_CONF_NM: str = ""  # 본회의 심의 회의명
    RGS_CONF_RSLT: str = ""  # 본회의 심의결과
    GVRN_TRSF_DT: str = ""  # 정부 이송일
    PROM_LAW_NM: str = ""  # 공포 법률명
    PROM_DT: str = ""  # 공포일
    PROM_NO: str = ""  # 공포번호
    LINK_URL: str = ""  # 링크URL

    # 메타데이터
    source_api: str = "ALLBILL"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
