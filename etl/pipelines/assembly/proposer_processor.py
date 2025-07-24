import asyncio
import json
import logging
from typing import Optional

from exceptions.exceptions import DataValidationError
from utils.file.fileio import read_file, write_file

logger = logging.getLogger(__name__)


class BillProposerProcessor:
    """의안 발의자 처리기"""

    def __init__(self, config, default_age: str = "22"):
        self.member_resolver = MemberIdResolver(f"{config.assembly_ref}/member_id.json")
        self.default_age = default_age

    async def process(self, data_paths: str, is_save: bool = True) -> list[dict]:
        """의안 발의자 관계 데이터 생성"""
        rst_proposers, co_proposers = await self._get_bill_proposers(data_paths)
        tasks = [
            self._process_proposers(rst_proposers, is_rst=True),
            self._process_proposers(co_proposers, is_rst=False),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        bill_proposers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(str(result))
            else:
                bill_proposers.extend(result)

        if is_save:
            await self.save(bill_proposers)
            return self.output_dir
        return bill_proposers

    async def _get_bill_proposers(self, data_paths: str) -> list[dict]:
        bills = await self._get_bills(data_paths)
        rst_proposers, co_proposers = [], []
        for bill_data in bills:
            bill_id = bill_data["BILL_ID"]
            rst_proposers.append((bill_id, bill_data["RST_PROPOSER"]))
            co_proposers.append((bill_id, bill_data["PUBL_PROPOSER"]))
        return rst_proposers, co_proposers

    async def _get_bills(self, data_paths: str) -> list[dict]:
        bills = []
        for api_name, path in data_paths:
            if api_name == "law_bill_member":
                data = await read_file(path)
                bills.extend(data)
        return bills

    async def _process_proposers(self, proposers: list[tuple], is_rst: bool) -> list[dict]:
        proposer_map = []
        for bill_id, proposer_str in proposers:
            if isinstance(proposer_str, str):
                proposer_names = [name.strip() for name in proposer_str.split(",")]
            member_ids = self.member_resolver.resolve_member_ids(proposer_names, self.default_age)
            proposer_map.extend(
                [{"BILL_ID": bill_id, "MEMBER_ID": member_id, "RST": is_rst} for member_id in member_ids]
            )
        return proposer_map
    
    async def save(self, data: list[dict]) -> None:
        try:
            await write_file(self.output_dir / "proposer_bill.json", data),
        except Exception as e:
            logger.error(f"Failed to save bill processors: {e}", exc_info=True)


class MemberIdResolver:
    """의원 ID 해결 클래스"""

    def __init__(self, member_id_file_path: str):
        self.member_dict = self._load_member_dict(member_id_file_path)

    def _load_member_dict(self, file_path: str) -> dict:
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
