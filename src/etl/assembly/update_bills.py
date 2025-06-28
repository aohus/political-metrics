import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from exceptions.exceptions import BillServiceError, DataProcessingError
from schema.utils import BillStatus
from sqlalchemy.exc import SQLAlchemyError

from ..utils import MemberIdResolver
from .bill_proposer_processor import BillProposerProcessor
from .bill_transformer import BillDataTransformer


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


class BillDataService:
    """의안 데이터 서비스 메인 클래스"""

    def __init__(
        self,
        config: BillServiceConfig = None,
    ):
        self.config = config or BillServiceConfig()

        # 의존성 초기화
        self.member_resolver = MemberIdResolver(self.config.member_id_file_path)
        self.data_transformer = BillDataTransformer(self.config)
        self.proposer_processor = BillProposerProcessor(
            self.member_resolver, self.config.default_age
        )

        self.logger = logging.getLogger(__name__)

    def process_bill_data(
        self, raw_data: Dict[str, List]
    ) -> Tuple[List[Bill], List[BillDetail], List[BillProposer]]:
        """원시 데이터를 처리하여 ORM 객체로 변환"""
        try:
            # 데이터 변환
            all_bills_data = self._transform_all_data(raw_data)

            # ORM 객체 생성
            bills = []
            bill_details = []
            bill_proposers = []

            for bill_data in all_bills_data:
                # 의안 상태 결정
                bill_data["STATUS"] = self.data_transformer.determine_bill_status(
                    bill_data
                )
                bill_data["COMMITTEE_NAME"] = bill_data.get("COMMITTEE")

                # ORM 객체 생성
                bills.append(Bill(**self._extract_bill_fields(bill_data)))
                bill_details.append(
                    BillDetail(**self._extract_bill_detail_fields(bill_data))
                )

                # 발의자 관계 처리
                proposers = self.proposer_processor.process_bill_proposers(bill_data)
                bill_proposers.extend(proposers)

            self.logger.info(
                f"Processed {len(bills)} bills, {len(bill_proposers)} proposer relationships"
            )

            return bills, bill_details, bill_proposers

        except Exception as e:
            raise DataProcessingError(f"Failed to process bill data: {e}") from e

    def _transform_all_data(self, raw_data: Dict[str, List]) -> List[Dict]:
        """모든 원시 데이터 변환"""
        all_bills = []

        # 의원 발의 데이터
        if "law_bill_member" in raw_data:
            member_bills = self.data_transformer.transform_member_bills(
                raw_data["law_bill_member"]
            )
            all_bills.extend(member_bills)

        # 정부 발의 데이터
        if "law_bill_gov" in raw_data:
            gov_bills = self.data_transformer.transform_government_bills(
                raw_data["law_bill_gov"]
            )
            all_bills.extend(gov_bills)

        # 기타 데이터 처리 (필요시 확장)
        if "law_bill_cap" in raw_data:
            # 추후 구현
            pass

        return all_bills

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
