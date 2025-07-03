from enum import Enum


class BillStatus(str, Enum):
    """의안 상태 열거형"""

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
    """성별 열거형"""

    MALE = "남"
    FEMALE = "여"


class ProposerType(str, Enum):
    """발의자 유형"""

    MEMBER = "의원"
    GOVERNMENT = "정부"
    COMMITTEE = "위원장"
