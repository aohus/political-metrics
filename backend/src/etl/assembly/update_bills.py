import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from exceptions.exceptions import BillServiceError, DataProcessingError
from schema.utils import BillStatus
from sqlalchemy.exc import SQLAlchemyError

from ..utils import MemberIdResolver
from .bill_proposer_processor import BillProposerProcessor
from .bill_transformer import BillDataTransformer

logger = logging.getLogger(__name__)


@dataclass
class BillServiceConfig:
    """의안 서비스 설정"""

    member_id_file_path: str = "../initial_scripts/data/new/member_id.json"
    default_age: str = "22"
    date_format: str = "%Y-%m-%d"

    # 의안 상태 매핑 규칙
    status_mapping: Dict[str, str] = None

    def __post_init__(self):
        if self.status_mapping is None:
            self.status_mapping = {
                "COMMITTEE_DT": BillStatus.COMMITTEE_IN_PROGRESS,
                "CMT_PRESENT_DT": BillStatus.COMMITTEE_IN_PROGRESS,
                "LAW_SUBMIT_DT": BillStatus.LEGISLATION_IN_PROGRESS,
                "LAW_PRESENT_DT": BillStatus.LEGISLATION_IN_PROGRESS,
            }


import json


class BillProcessor:
    def __init__(self, config):
        self.config = config
        self.date_converter = DateConverter()

    async def _read_data(path: str) -> dict:
        with open(path, "r") as f:
            data = json.load(f)
        return data

    async def process(self, path_list: list):
        for api_name, path in path_list:
            self.transform(api_name, path)

    async def transform(self, api_name: str, path: str):
        if api_name == "law_bills_member":
            self._transform_member_bills(path)
        elif api_name == "law_bills_gov":
            self._transform_gov_bills(path)
        else:
            pass

    async def convert_to_table(self, bills: list):
        for bill in bills:
            bill["STATUS"] = self.determine_status(bill)
            bill["COMMITTEE_NAME"] = bill.get("COMMITTEE")

            bill = extract_bill(bill)
            bill_detail = extract_bill_detail(bill)
            proposer = self.process_bill_proposer(bill)

    def _extract_bill_fields(self, bill_data: Dict) -> Dict:
        """Bill 모델에 필요한 필드만 추출"""
        bill_fields = [
            "BILL_ID",
            "BILL_NO",
            "AGE",
            "BILL_NAME",
            "COMMITTEE_NAME",
            "PROPOSE_DT",
            "PROC_DT",
            "STATUS",
        ]

        return {
            field: bill_data.get(field) for field in bill_fields if field in bill_data
        }

    def _extract_bill_detail_fields(self, bill_data: Dict) -> Dict:
        """BillDetail 모델에 필요한 필드만 추출"""
        detail_fields = [
            "BILL_ID",
            "PROC_DT",
            "DETAIL_LINK",
            "LAW_SUBMIT_DT",
            "LAW_PRESENT_DT",
            "LAW_PROC_DT",
            "LAW_PROC_RESULT_CD",
            "COMMITTEE_DT",
            "CMT_PRESENT_DT",
            "CMT_PROC_DT",
            "CMT_PROC_RESULT_CD",
            "PROC_RESULT",
        ]

        return {
            field: bill_data.get(field) for field in detail_fields if field in bill_data
        }

    def _transform_member_bills(self, data: List[RawLawBillMemberData]) -> List[Dict]:
        """의원 발의 의안 데이터 변환"""
        transformed_bills = []
        for bill in data:
            bill_dict = dict(bill)
            bill_dict["PROPOSER_KIND"] = ProposerType.MEMBER
            transformed_bills.append(bill_dict)
        return transformed_bills

    def _transform_government_bills(self, data: List[RawLawBillAllData]) -> List[Dict]:
        """정부/위원장 발의 의안 데이터 변환"""
        convert_mapping = {
            "CURR_COMMITTEE_ID": "COMMITTEE_ID",
            "CURR_COMMITTEE": "COMMITTEE",
            "PROC_RESULT_CD": "PROC_RESULT",
            "LINK_URL": "DETAIL_LINK",
        }

        transformed_bills = []
        for bill in data:
            # 필드명 변환
            bill_dict = {convert_mapping.get(k, k): v for k, v in bill.items()}
            if bill_dict["PROPOSER_KIND"] == "정부":
                proposer_kind = ProposerType.GOVERNMENT
            else:
                proposer_kind = ProposerType.COMMITTEE
            # 정부 발의 특성 추가
            bill_dict["PUBL_PROPOSER"] = None
            bill_dict["MEMBER_LIST"] = None
            bill_dict["PROPOSER_KIND"] = proposer_kind

            # 불필요한 필드 제거
            fields_to_remove = ["COMMITTEE_PROC_DT", "RST_MONA_CD"]
            for field in fields_to_remove:
                bill_dict.pop(field, None)

            transformed_bills.append(bill_dict)

        return transformed_bills

    def determine_bill_status(self, bill_data: Dict) -> str:
        """의안 상태 결정"""
        try:
            # 이미 처리 결과가 있는 경우
            if bill_data.get("PROC_RESULT"):
                return bill_data["PROC_RESULT"]

            # 위원회가 지정되지 않은 경우
            if not bill_data.get("COMMITTEE"):
                return BillStatus.WAITING_COMMITTEE

            # 처리 단계별 상태 결정
            return self._calculate_status_by_process_stage(bill_data)

        except Exception as e:
            self.logger.error(f"Error determining bill status: {e}")
            return BillStatus.OTHER

    def _calculate_status_by_process_stage(self, bill_data: Dict) -> str:
        """처리 단계별 상태 계산"""
        status_fields = [
            "COMMITTEE_DT",
            "CMT_PRESENT_DT",
            "CMT_PROC_DT",
            "LAW_SUBMIT_DT",
            "LAW_PRESENT_DT",
            "LAW_PROC_DT",
        ]

        # None이 아닌 필드들만 필터링
        process_stages = {
            field: bill_data[field]
            for field in status_fields
            if bill_data.get(field) is not None
        }

        stage_count = len(process_stages)
        today = self.date_converter.now_isoformat()

        # 단계별 상태 매핑
        status_rules = {
            1: BillStatus.COMMITTEE_IN_PROGRESS,
            2: self._check_committee_status(bill_data, today),
            3: BillStatus.LEGISLATION_IN_PROGRESS,
            4: BillStatus.LEGISLATION_IN_PROGRESS,
            5: self._check_legislation_status(bill_data, today),
        }

        return status_rules.get(stage_count, BillStatus.OTHER)

    def _check_committee_status(self, bill_data: Dict, today: str) -> str:
        """소관위 상태 확인"""
        present_dt = bill_data.get("CMT_PRESENT_DT")
        if present_dt and today < self.date_converter.str_to_isoformat(present_dt):
            return BillStatus.COMMITTEE_PENDING
        return BillStatus.COMMITTEE_IN_PROGRESS

    def _check_legislation_status(self, bill_data: Dict, today: str) -> str:
        """법사위 상태 확인"""
        present_dt = bill_data.get("LAW_PRESENT_DT")
        if present_dt and today < self.date_converter.str_to_isoformat(present_dt):
            return BillStatus.LEGISLATION_PENDING
        return BillStatus.LEGISLATION_IN_PROGRESS


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
