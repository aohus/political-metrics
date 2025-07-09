import logging
import json

from core.exceptions.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class BillProposerProcessor:
    """의안 발의자 처리기"""

    def __init__(self, assembly_ref: str, default_age: str = "22"):
        self.member_resolver = MemberIdResolver(f"{assembly_ref}/member_id.json")
        self.default_age = default_age

    async def process_bill_proposers(self, bills: list[dict]) -> list[dict]:
        """의안 발의자 관계 데이터 생성"""
        proposers = []
        for bill_data in bills:
            bill_id = bill_data["BILL_ID"]
            proposers.extend(await self._process_lead_proposers(bill_id, bill_data))
            proposers.extend(await self._process_co_proposers(bill_id, bill_data))
        return proposers

    async def _process_lead_proposers(self, bill_id: str, bill_data: Dict) -> list[dict]:
        proposers = []
        rst_proposers = bill_data.get("RST_PROPOSER")

        if not rst_proposers:
            return proposers

        if isinstance(rst_proposers, str):
            rst_proposers = [name.strip() for name in rst_proposers.split(",")]

        member_ids = self.member_resolver.resolve_member_ids(rst_proposers, self.default_age)
        for member_id in member_ids:
            proposers.append({"BILL_ID": bill_id, "MEMBER_ID": member_id, "RST": True})
        return proposers

    async def _process_co_proposers(self, bill_id: str, bill_data: dict) -> list[dict]:
        """공동발의자 처리"""
        proposers = []
        co_proposers_str = bill_data.get("PUBL_PROPOSER")

        if not co_proposers_str:
            return proposers

        co_proposer_names = [name.strip() for name in co_proposers_str.split(",")]
        member_ids = self.member_resolver.resolve_member_ids(co_proposer_names, self.default_age)

        for member_id in member_ids:
            proposers.append({"BILL_ID": bill_id, "MEMBER_ID": member_id, "RST": False})
        return proposers


class MemberIdResolver:
    """의원 ID 해결 클래스"""

    def __init__(self, member_id_file_path: str):
        self.member_dict = self._load_member_dict(member_id_file_path)

    def _load_member_dict(self, file_path: str) -> dict:
        """의원 ID 매핑 딕셔너리 로드"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Member ID file not found: {file_path}")
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
                logger.warning(f"Member ID not found for: {name} (age: {age})")
        return resolved_ids
