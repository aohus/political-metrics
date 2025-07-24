from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class BillStatus(str, Enum):
    WAITING = "위원회지정대기"
    ORIGINAL_PASSED = "원안가결"
    AMENDED_PASSED = "수정가결"
    AMENDED_DISCARDED = "수정안반영폐기"
    ALTERNATIVE_DISCARDED = "대안반영폐기"
    COMMITTEE_PENDING = "위원회계류"
    LEGISLATION_PENDING = "체계자구계류"
    COMMITTEE_IN_PROGRESS = "위원회심사"
    LEGISLATION_IN_PROGRESS = "체계자구심사"
    REJECTED = "부결"
    RECONSIDERATION_REJECTED = "제의부결"
    GOVERNMENT_RECONSIDERATION = "정부제의"
    WITHDRAWN = "철회"
    OTHER = "기타"


class Gender(str, Enum):
    MALE = "남"
    FEMALE = "여"


class ProposerType(str, Enum):
    MEMBER = "의원"
    GOVERNMENT = "정부"
    COMMITTEE = "위원장"

@dataclass
class Bill:
    BILL_ID: str
    BILL_NO: str
    AGE: Optional[str] = None
    BILL_NAME: str = ""
    ALTER_BILL_NO: Optional[str] = None
    COMMITTEE_NAME: Optional[str] = None
    PROPOSE_DT: Optional[datetime] = None
    PROC_DT: Optional[datetime] = None
    STATUS: BillStatus = BillStatus.COMMITTEE_PENDING


@dataclass
class BillDetail:
    BILL_ID: str
    PROC_DT: Optional[datetime] = None
    DETAIL_LINK: Optional[str] = None
    LAW_SUBMIT_DT: Optional[datetime] = None
    LAW_PRESENT_DT: Optional[datetime] = None
    LAW_PROC_DT: Optional[datetime] = None
    LAW_PROC_RESULT_CD: Optional[str] = None
    COMMITTEE_DT: Optional[str] = None
    CMT_PRESENT_DT: Optional[datetime] = None
    CMT_PROC_DT: Optional[datetime] = None
    CMT_PROC_RESULT_CD: Optional[str] = None
    PROC_RESULT: Optional[str] = None
    GVRN_TRSF_DT: Optional[datetime] = None
    PROM_LAW_NM: Optional[str] = None
    PROM_DT: Optional[datetime] = None
    PROM_NO: Optional[str] = None


@dataclass
class BillProposer:
    BILL_ID: str
    MEMBER_ID: str
    RST: bool = False
