from enum import Enum


class BillStatus(str, Enum):
    """의안 상태 열거형"""

    WITHDRAWN = "철회"
    ORIGINAL_PASSED = "원안가결"
    AMENDED_PASSED = "수정가결"
    AMENDED_DISCARDED = "수정안반영폐기"
    ALTERNATIVE_DISCARDED = "대안반영폐기"
    REJECTED = "부결"
    WAITING = "소관위원회지정대기"
    COMMITTEE_PENDING = "소관위계류"
    LEGISLATION_PENDING = "법사위계류"
    COMMITTEE_IN_PROGRESS = "소관위진행중"
    LEGISLATION_IN_PROGRESS = "법사위진행중"
    OTHER = "기타"


class Gender(str, Enum):
    """성별 열거형"""

    MALE = "남"
    FEMALE = "여"


class ProposerType(str, Enum):
    """발의자 유형"""

    MEMBER = "의원"
    GOVERNMENT = "정부"
    COMMITTEE = "위원장"
