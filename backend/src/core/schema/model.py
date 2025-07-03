import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator
from schema.utils import BillStatus, Gender

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ Pydantic 모델들 ============
class MemberHistory(BaseModel):
    """국회의원 정보"""

    AGE: str = Field(..., description="당선대수")
    MEMBER_ID: str = Field(..., description="국회의원코드", max_length=50)
    DTY_NM: Optional[str] = Field(None, description="직책명", max_length=100)
    ELECD_NM: Optional[str] = Field(None, description="선거구명", max_length=100)
    ELECD_DIV_NM: Optional[str] = Field(None, description="선거구구분명", max_length=50)
    PLPT_NM: Optional[str] = Field(None, description="정당명", max_length=100)
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="생성일시"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "AGE": "22",
                "MEMBER_ID": "MP001",
                "PLPT_NM": "더불어민주당",
                "ELECD_NM": "서울 강남구 갑",
            }
        }
    )


class Member(BaseModel):
    """국회의원 정보"""

    MEMBER_ID: str = Field(..., description="국회의원코드", max_length=50)
    NAAS_NM: str = Field(..., description="국회의원명", max_length=100)
    BIRDY_DT: Optional[str] = Field(None, description="생일일자", max_length=20)
    DTY_NM: Optional[str] = Field(None, description="직책명", max_length=100)
    PLPT_NM: Optional[str] = Field(None, description="정당명", max_length=100)
    ELECD_NM: Optional[str] = Field(None, description="선거구명", max_length=100)
    ELECD_DIV_NM: Optional[str] = Field(None, description="선거구구분명", max_length=50)
    CMIT_NM: Optional[str] = Field(None, description="위원회명", max_length=200)
    BLNG_CMIT_NM: Optional[str] = Field(None, description="소속위원회명")
    RLCT_DIV_NM: Optional[str] = Field(None, description="재선구분명", max_length=50)
    GTELT_ERACO: Optional[str] = Field(None, description="당선대수", max_length=100)
    NTR_DIV: Optional[Gender] = Field(None, description="성별")
    NAAS_HP_URL: Optional[str] = Field(
        None, description="국회의원홈페이지URL", max_length=500
    )
    BRF_HST: Optional[str] = Field(None, description="약력")
    NAAS_PIC: Optional[str] = Field(None, description="국회의원 사진", max_length=500)
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="생성일시"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "MEMBER_ID": "MP001",
                "NAAS_NM": "김의원",
                "PLPT_NM": "더불어민주당",
                "ELECD_NM": "서울 강남구 갑",
                "NTR_DIV": "남",
            }
        },
    )


class Bill(BaseModel):
    """의안 정보"""

    BILL_ID: str = Field(..., description="의안ID", max_length=100)
    BILL_NO: str = Field(..., description="의안번호", max_length=50)
    AGE: str = Field("", description="대수", max_length=10)
    BILL_NAME: str = Field(..., description="법률안명", max_length=500)
    COMMITTEE_NAME: Optional[str] = Field(None, description="소관위원회")
    PROPOSE_DT: Optional[datetime] = Field(None, description="제안일")
    PROC_DT: Optional[datetime] = Field(None, description="의결일")
    ALTER_BILL_NO: Optional[str] = Field(None, description="의안번호", max_length=50)
    STATUS: BillStatus = Field(BillStatus.COMMITTEE_PENDING, description="의안상태")

    @field_validator("BILL_NAME")
    @classmethod
    def validate_bill_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("의안명은 2자 이상이어야 합니다")
        return v.strip()

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "BILL_ID": "BILL001",
                "BILL_NO": "2210001",
                "BILL_NAME": "스토킹범죄의 처벌 등에 관한 법률 일부개정법률안",
                "AGE": "22",
                "COMMITTEE_NAME": "중소기업",
                "STATUS": "소관위계류",
            }
        },
    )


class BillDetail(BaseModel):
    """의안 상세 정보"""

    BILL_ID: str = Field(..., description="의안ID", max_length=100)
    PROC_DT: Optional[datetime] = Field(None, description="의결일")
    DETAIL_LINK: Optional[str] = Field(None, description="상세페이지", max_length=1000)
    LAW_SUBMIT_DT: Optional[datetime] = Field(None, description="법사위회부일")
    LAW_PRESENT_DT: Optional[datetime] = Field(None, description="법사위상정일")
    LAW_PROC_DT: Optional[datetime] = Field(None, description="법사위처리일")
    LAW_PROC_RESULT_CD: Optional[str] = Field(
        None, description="법사위처리결과", max_length=50
    )
    COMMITTEE_DT: Optional[datetime] = Field(None, description="소관위회부일")
    CMT_PRESENT_DT: Optional[datetime] = Field(None, description="소관위상정일")
    CMT_PROC_DT: Optional[datetime] = Field(None, description="소관위처리일")
    CMT_PROC_RESULT_CD: Optional[str] = Field(
        None, description="소관위처리결과", max_length=50
    )
    PROC_RESULT: Optional[str] = Field(
        None, description="본회의심의결과", max_length=100
    )
    GVRN_TRSF_DT: Optional[datetime] = Field(None, description="정부 이송일")
    PROM_LAW_NM: Optional[str] = Field(None, description="공포 법률명", max_length=500)
    PROM_DT: Optional[datetime] = Field(None, description="공포일")
    PROM_NO: Optional[str] = Field(None, description="공포번호", max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "BILL_ID": "BILL001",
                "PROC_RESULT": "심사중",
                "DETAIL_LINK": "https://likms.assembly.go.kr/bill/detail",
            }
        }
    )


class BillProposer(BaseModel):
    """의안 발의자 관계"""

    BILL_ID: str = Field(..., description="의안ID", max_length=100)
    MEMBER_ID: str = Field(..., description="정치인ID", max_length=50)
    RST: bool = Field(False, description="대표발의자 여부")


class Committee(BaseModel):
    """위원회 정보"""

    COMMITTEE_ID: Optional[str] = Field(..., description="위원회ID")
    COMMITTEE_NAME: str = Field(..., description="위원회명", max_length=200)
    COMMITTEE_TYPE: str = Field("", description="위원회유형", max_length=50)
    COMMITTEE_TYPE_CODE: str = Field("", description="위원회유형코드", max_length=20)
    LIMIT_CNT: Optional[int] = Field(..., description="위원정수")
    CURR_CNT: Optional[int] = Field(..., description="현원")
    POLY99_CNT: Optional[int] = Field(..., description="비교섭단체위원수")
    POLY_CNT: Optional[int] = Field(..., description="교섭단체위원수")
    ORDER_NUM: Optional[str] = Field(..., description="순서")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "COMMITTEE_ID": "1",
                "COMMITTEE_NAME": "법제사법위원회",
                "COMMITTEE_TYPE": "상임위원회",
            }
        }
    )


class CommitteeMember(BaseModel):
    """위원회 구성원"""

    COMMITTEE_NAME: str = Field(..., description="위원회이름")
    MEMBER_ID: str = Field(..., description="의원ID", max_length=50)
    MEMBER_TYPE: Optional[str] = Field(
        None, description="의원유형", max_length=50
    )  # 위원장/위원/간사
