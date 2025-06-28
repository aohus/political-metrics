class BillServiceError(Exception):
    """의안 서비스 기본 예외"""

    pass


class DataValidationError(BillServiceError):
    """데이터 검증 예외"""

    pass


class DataProcessingError(BillServiceError):
    """데이터 처리 예외"""

    pass
