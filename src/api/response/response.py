from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from ..service.analyzer import (
    BillStatistics,
    MemberBillStatistics,
    MemberCommitteeStatistics,
)


class MemberResponse(BaseModel):
    MEMBER_ID: str = Field(..., description="의원ID")
    NAAS_NM: str = Field(..., description="의원명")
    BIRDY_DT: Optional[str] = None
    PLPT_NM: Optional[str] = None
    ELECD_DIV_NM: Optional[str] = None
    CMIT_NM: Optional[str] = None
    NAAS_PIC: Optional[str] = None


class MemberStatisticsResponse(BaseModel):
    member_info: MemberResponse = None
    bill_stats: Optional[MemberBillStatistics] = None
    committee_stats: Optional[list[MemberCommitteeStatistics]] = None
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BillStatisticsResponse(BaseModel):
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
            MemberStatisticsResponse,
            list[MemberStatisticsResponse],
            list[BillStatistics],
        ]
    ] = Field(
        None, description="응답 데이터"
    )  # data 타입 확장
    total: Optional[int] = Field(None, description="총 개수")
