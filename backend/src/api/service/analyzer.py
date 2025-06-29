from dataclasses import dataclass
from typing import Optional


@dataclass
class MemberBillStatistic:
    total_count: int
    total_pass_rate: float
    lead_count: int
    lead_pass_rate: float
    co_count: int
    co_pass_rate: float
    # avg_processing_days: float = Field(0.0, description="평균 처리기간(일)")


@dataclass
class MemberCommitteeStatistic:
    active_committee: str
    total_count: int
    lead_count: int
    co_count: int


@dataclass
class BillStatistic:
    bill_code: str
    bill_name: str
    bill_committee: str
    bill_count: int
    bill_pass_rate: float


class MemberStatisticsCalculator:
    def get_member_statistics(self, member_id: str): ...

    def calculate_bill_statistics(
        self, member_id: str
    ) -> list[MemberBillStatistic]: ...

    def calculate_committee_statistics(
        self, member_id: str
    ) -> list[MemberCommitteeStatistic]: ...

    def get_top_members_by_criteria(
        self, criterial: str, limit: int = 10
    ) -> list[MemberBillStatistic]: ...


class BillStatisticsCalculator:
    def get_top_bills_by_criteria(self, criteria: str, limit: int = 10): ...


class CommitteeStatisticsCalculator:
    def get_top_bills_by_criteria(self, criteria: str, limit: int = 10): ...
