from datetime import datetime
from core.exceptions.exceptions import DataValidationError


class DateConverter:
    """날짜 변환 유틸리티"""

    @staticmethod
    def str_to_isoformat(date_str: str, date_format: str = "%Y-%m-%d") -> str:
        """문자열 날짜를 ISO 형식으로 변환"""
        try:
            if not date_str:
                return None
            date_obj = datetime.strptime(date_str, date_format).date()
            return date_obj.isoformat()
        except ValueError as e:
            raise DataValidationError(f"Invalid date format: {date_str}") from e

    @staticmethod
    def now_isoformat() -> str:
        """현재 시간을 ISO 형식으로 반환"""
        return datetime.now().isoformat()
