import logging
from typing import Dict, List

from schema.utils import BillStatus, ProposerType
from service.collector.update_bills import BillServiceConfig
from service.collector.utils import DateConverter

from src.etl.utils.extract.raw_data_model import RawLawBillAllData, RawLawBillMemberData


class BillDataTransformer:
    """의안 데이터 변환기"""

    def __init__(self, config: BillServiceConfig):
        self.config = config
        self.date_converter = DateConverter()
        self.logger = logging.getLogger(__name__)

    def transform_member_bills(self, data: List[RawLawBillMemberData]) -> List[Dict]:
        """의원 발의 의안 데이터 변환"""
        transformed_bills = []
        for bill in data:
            bill_dict = dict(bill)
            bill_dict["PROPOSER_KIND"] = ProposerType.MEMBER
            transformed_bills.append(bill_dict)
        return transformed_bills

    def transform_government_bills(self, data: List[RawLawBillAllData]) -> List[Dict]:
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
