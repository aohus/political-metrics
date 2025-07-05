import json
import logging
from datetime import datetime
from typing import Optional

from core.exceptions.exceptions import (
    BillServiceError,
    DataProcessingError,
    DataValidationError,
)


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


class MemberIdResolver:
    """의원 ID 해결 클래스"""

    def __init__(self, member_id_file_path: str):
        self.logger = logging.getLogger(__name__)
        self.member_dict = self._load_member_dict(member_id_file_path)

    def _load_member_dict(self, file_path: str) -> dict:
        """의원 ID 매핑 딕셔너리 로드"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Member ID file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            raise DataValidationError(f"Invalid JSON in member ID file: {e}")

    def get_member_id(self, member_name: str, age: str) -> Optional[str]:
        """의원명과 대수로 의원 ID 조회"""
        return self.member_dict.get(str((member_name, age)))

    def resolve_member_ids(self, member_names: list[str], age: str) -> list[str]:
        """의원명 목록을 의원 ID 목록으로 변환"""
        resolved_ids = []
        for name in member_names:
            member_id = self.get_member_id(name.strip(), age)
            if member_id:
                resolved_ids.append(member_id)
            else:
                self.logger.warning(f"Member ID not found for: {name} (age: {age})")
        return resolved_ids
