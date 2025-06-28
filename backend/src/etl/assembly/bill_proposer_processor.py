import logging
from typing import Dict, List

from schema.model import BillProposer
from service.collector.utils import MemberIdResolver


class BillProposerProcessor:
    """의안 발의자 처리기"""

    def __init__(self, member_resolver: MemberIdResolver, default_age: str):
        self.member_resolver = member_resolver
        self.default_age = default_age
        self.logger = logging.getLogger(__name__)

    def process_bill_proposers(self, bill_data: Dict) -> List[BillProposer]:
        """의안 발의자 관계 데이터 생성"""
        proposers = []
        bill_id = bill_data["BILL_ID"]

        # 대표발의자 처리
        proposers.extend(self._process_lead_proposers(bill_id, bill_data))

        # 공동발의자 처리
        proposers.extend(self._process_co_proposers(bill_id, bill_data))

        return proposers

    def _process_lead_proposers(
        self, bill_id: str, bill_data: Dict
    ) -> List[BillProposer]:
        """대표발의자 처리"""
        proposers = []
        rst_proposers = bill_data.get("RST_PROPOSER")

        if not rst_proposers:
            return proposers

        # 리스트가 아닌 경우 리스트로 변환
        if isinstance(rst_proposers, str):
            rst_proposers = [rst_proposers]

        member_ids = self.member_resolver.resolve_member_ids(
            rst_proposers, self.default_age
        )

        for member_id in member_ids:
            proposers.append(
                BillProposer(BILL_ID=bill_id, MEMBER_ID=member_id, RST=True)
            )

        return proposers

    def _process_co_proposers(
        self, bill_id: str, bill_data: Dict
    ) -> List[BillProposer]:
        """공동발의자 처리"""
        proposers = []
        co_proposers_str = bill_data.get("PUBL_PROPOSER")

        if not co_proposers_str:
            return proposers

        co_proposer_names = [name.strip() for name in co_proposers_str.split(",")]
        member_ids = self.member_resolver.resolve_member_ids(
            co_proposer_names, self.default_age
        )

        for member_id in member_ids:
            proposers.append(
                BillProposer(BILL_ID=bill_id, MEMBER_ID=member_id, RST=False)
            )

        return proposers
