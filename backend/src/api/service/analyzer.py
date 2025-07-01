import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters.adapters import BillAdapter, MemberAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemberService:
    def __init__(self, adapter: MemberAdapter, db_session: AsyncSession):
        self.adapter = adapter(db_session)

    async def get_members(self, limit: int = 20, age: str = None, party: Optional[str] = None) -> list:
        return await self.adapter.get_members(limit, age, party)

    async def get_member(self, member_id: str) -> Optional[dict]:
        tasks = [
            self.adapter.get_member_by_id(member_id),
            self.adapter.get_member_bill_statistics(member_id),
            self.adapter.get_member_committee_statistics(member_id)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        if any(isinstance(result, Exception) for result in results):
            logger.error(f"Error fetching member data for {member_id}: {results}")
            return None

        return {
            "member": results[0],
            "bill_stats": results[1],
            "committee_stats": results[2]
        }

    async def get_top_members_by_criteria(self, criteria: str, limit: int = 10) -> list[dict]:
        top_members = await self.adapter.get_top_members_by_criteria(criteria, limit)
        tasks = [self.get_member(member.MEMBER_ID) for member in top_members]
        results = await asyncio.gather(*tasks)
        return results


class BillService:
    def __init__(self, adapter: BillAdapter, db_session: AsyncSession):
        self.adapter = adapter(db_session)

    async def get_top_bills_by_criteria(self, criteria: str, limit: int = 10):
        return self.adapter.get_top_bills_by_criteria(criteria, limit)


class CommitteeServie:
    async def get_top_bills_by_criteria(self, criteria: str, limit: int = 10): ...
