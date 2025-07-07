import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from ..repository.repository import BillRepository, MemberRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemberService:
    def __init__(self, repo: MemberRepository):
        self.repo = repo

    async def validate_criteria(self, criteria: str):
        valid_criteria = ["total_count", "total_pass_rate", "lead_count", "lead_pass_rate", "co_count", "co_pass_rate"]
        if criteria not in valid_criteria:
            raise ValueError(f"Invalid criteria: {criteria}. Must be one of {valid_criteria}")
        
    async def get_members(self, age: str = "22", party: Optional[str] = None, committee: Optional[str] = None, limit: int = 10) -> list:
        return await self.repo.get_members(limit, age, party, committee)

    async def get_member(self, member_id: str) -> Optional[dict]:
        return await self.repo.get_member_info(member_id)

    async def get_top_members_by_criteria(self, criteria: str, party: Optional[str] = None, committee: Optional[str] = None, limit: int = 10) -> list[dict]:
        await self.validate_criteria(criteria)
        top_members = await self.repo.get_top_members_by_criteria(criteria, party, committee, limit)
        return top_members


class BillService:
    def __init__(self, repo: BillRepository):
        self.repo = repo

    async def validate_criteria(self, criteria: str):
        valid_criteria = ["proposed", "passed", "proposed_by_committee"]
        if criteria not in valid_criteria:
            raise ValueError(f"Invalid criteria: {criteria}. Must be one of {valid_criteria}")

    async def get_bills(self, limit: int = 20, age: str = "22", party: Optional[str] = None) -> list:
        return await self.repo.get_bills(limit, age, party)
    
    async def get_top_bills_by_criteria(self, criteria: str = "proposed", party: Optional[str] = None, committee: Optional[str] = None, limit: int = 10, ) -> list[dict]:
        await self.validate_criteria(criteria)
        return await self.repo.get_top_bills_by_criteria(criteria, party, committee, limit)


class CommitteeServie:
    async def get_top_bills_by_criteria(self, criteria: str, limit: int = 10): ...
