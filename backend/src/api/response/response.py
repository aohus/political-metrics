from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class MemberResponse(BaseModel):
    NAAS_NM: str = Field(..., description="의원명")
    BIRDY_DT: Optional[str] = None
    PLPT_NM: Optional[str] = None
    GTELT_ERACO: Optional[str] = None
    ELECD_NM: Optional[str] = None
    BLNG_CMIT_NM: Optional[str] = None
    NAAS_PIC: Optional[str] = None
    BRF_HST: Optional[str] = None
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class MemberBillStatistic(BaseModel):
    total_count: int
    total_pass_rate: float = Field(0.0, description="가결률(%)")
    lead_count: int
    lead_pass_rate: float = Field(0.0, description="가결률(%)")
    co_count: int
    co_pass_rate: float = Field(0.0, description="가결률(%)")
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class MemberCommitteeStatistic(BaseModel):
    active_committee: str
    total_count: int
    lead_count: int
    co_count: int


class BillStatistic(BaseModel):
    bill_code: str
    bill_name: str
    bill_committee: str
    bill_count: int
    bill_pass_rate: float
# avg_processing_days: float = Field(0.0, description="평균 처리기간(일)")


class MemberStatisticResponse(BaseModel):
    member_info: MemberResponse = None
    bill_stats: MemberBillStatistic = None
    committee_stats: list[MemberCommitteeStatistic] = None
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BillStatisticResponse(BaseModel):
    bill_code: str
    bill_name: str
    bill_committee: str
    bill_count: int
    bill_pass_rate: float = Field(0.0, description="가결률(%)")


# class BillResponse(BaseModel):
#     BILL_ID: str
#     BILL_NO: str
#     AGE: str
#     BILL_NAME: str
#     COMMITTEE_ID: Optional[str] = None
#     PROPOSE_DT: Optional[datetime] = None
#     PROC_DT: Optional[datetime] = None
#     STATUS: BillStatus
#     # BillDetail과 BillProposer에서 가져올 필드 추가
#     rst_proposer_name: Optional[str] = None  # 대표발의자 이름 (조인으로 가져올 필드)
#     proc_result: Optional[str] = None  # 본회의심의결과 (BillDetail에서 가져올 필드)

#     model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class APIResponse(BaseModel):
    """표준 API 응답 형식"""

    success: bool = Field(True, description="성공 여부")
    message: str = Field("", description="응답 메시지")
    data: Optional[
        Union[
            Dict[str, Any],
            List[Any],
            MemberStatisticResponse,
            list[MemberStatisticResponse],
            list[BillStatistic],
        ]
    ] = Field(
        None, description="응답 데이터"
    )  # data 타입 확장
    total: Optional[int] = Field(None, description="총 개수")
