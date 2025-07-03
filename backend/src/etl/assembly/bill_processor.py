import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import aiofiles
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from ...api.model.orm import Bill, BillDetail, BillProposer
from ...core.exceptions.exceptions import BillServiceError, DataProcessingError
from ...core.schema.utils import BillStatus, ProposerType
from ..utils import DateConverter, MemberIdResolver

logger = logging.getLogger(__name__)


with open("./data/assemply/ref/alter_bill_link.json", "r") as f:
    alter_bill_link = json.load(f)


async def read_data(path: str) -> dict:
    async with aiofiles.open(path, "r") as f:
        content = await f.read()
        data = json.loads(content)
    return data


class BillProcessor:
    def __init__(self, output_dir: str):
        self.date_converter = DateConverter()
        self.output_dir = output_dir

    async def process(self, path_list: list):
        tasks = [self.transform(api_name, path) for api_name, path in path_list]
        results = await asyncio.gather(*tasks, return_exception=True)
        merged_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(str(result))
                raise result
            else:
                merged_results.extend(result)
        return await self.convert_to_table_format(merged_results)

    async def transform(self, api_name: str, path: str) -> None:
        data = await read_data(path)
        handlers = {
            "law_bills_member": self._transform_member_bills,
            "law_bills_gov": self._transform_government_bills,
        }
        if handler := handlers.get(api_name):
            try:
                logger.info(f"Successfully transformed {api_name} data from {data}")
                return await handler(data)
            except Exception as e:
                logger.error(f"Failed to transform {api_name}: {e}")
                raise
        else:
            raise ValueError(f"Unsupported API type: {api_name}")

    async def _transform_member_bills(self, data: List[dict]) -> List[Dict]:
        df = pd.DataFrame(data)
        df["PROPOSER_KIND"] = ProposerType.MEMBER
        return df.to_dict(orient="records")

    async def _transform_government_bills(self, data: List[dict]) -> List[Dict]:
        convert_mapping = {
            "CURR_COMMITTEE_ID": "COMMITTEE_ID",
            "CURR_COMMITTEE": "COMMITTEE",
            "CMT_PROC_DT": "COMMITTEE_PROC_DT",
            "PROC_RESULT_CD": "PROC_RESULT",
            "LINK_URL": "DETAIL_LINK",
        }
        df = pd.DataFrame(data)
        df = df.rename(columns=convert_mapping)
        df["PROPOSER_KIND"] = df["PROPOSER_KIND"].apply(
            lambda x: ProposerType.GOVERNMENT if x == "정부" else ProposerType.COMMITTEE
        )
        df["PUBL_PROPOSER"] = None
        df["MEMBER_LIST"] = None
        df = df.drop(columns=["COMMITTEE_PROC_DT", "RST_MONA_CD"], errors="ignore")
        return df.to_dict(orient="records")

    async def convert_to_table_format(self, bills: list):
        bill_dict, bill_detail_dict = {}, {}
        for bill in bills:
            bill["COMMITTEE_NAME"] = bill.get("COMMITTEE")
            bill["STATUS"] = self._determine_bill_status(bill)
            if bill["STATUS"] in [BillStatus.AMENDED_DISCARDED, BillStatus.ALTERNATIVE_DISCARDED]:
                bill["ALTER_BILL_NO"] = self._link_alter_bill_no(bill["BILL_NO"])

            bill_dict.append({field: bill.get(field, None) for field in Bill.__table__.columns.keys()})
            bill_detail_dict.append({field: bill.get(field, None) for field in BillDetail.__table__.columns.keys()})
        return [("bills", bill_dict), ("bill_details", bill_detail_dict)]

    async def _link_alter_bill_no(self, bill_data: dict) -> list:
        return alter_bill_link[bill_data["BILL_NO"]]

    async def _determine_bill_status(self, bill_data: Dict) -> str:
        """의안 상태 결정"""
        try:
            # 위원회가 지정되지 않은 경우
            if not bill_data.get("COMMITTEE"):
                return BillStatus.WAITING_COMMITTEE
            # 이미 처리 결과가 있는 경우
            if bill_data.get("PROC_RESULT"):
                return bill_data["PROC_RESULT"]

            # 처리 단계별 상태 결정
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
        except Exception as e:
            logger.error(f"Error determining bill status: {e}")
            return BillStatus.OTHER

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

    def __init__(self, member_resolver: MemberIdResolver, default_age: str = "22"):
        self.member_resolver = member_resolver
        self.default_age = default_age

    async def process_bill_proposers(self, bill_data: Dict) -> List[BillProposer]:
        """의안 발의자 관계 데이터 생성"""
        proposers = []
        bill_id = bill_data["BILL_ID"]
        proposers.extend(await self._process_lead_proposers(bill_id, bill_data))
        proposers.extend(await self._process_co_proposers(bill_id, bill_data))
        return proposers

    async def _process_lead_proposers(
        self, bill_id: str, bill_data: Dict
    ) -> List[BillProposer]:
        proposers = []
        rst_proposers = bill_data.get("RST_PROPOSER")

        if not rst_proposers:
            return proposers

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

    async def _process_co_proposers(
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


    # def _extract_bill_fields(self, bill_data: Dict) -> Dict:
    #     """Bill 모델에 필요한 필드만 추출"""
    #     bill_fields = [
    #         "BILL_ID",
    #         "BILL_NO",
    #         "AGE",
    #         "BILL_NAME",
    #         "COMMITTEE_NAME",
    #         "PROPOSE_DT",
    #         "PROC_DT",
    #         "STATUS",
    #         "ALTER_BILL_NO",
    #     ]

    #     return {
    #         field: bill_data.get(field) for field in bill_fields if field in bill_data
    #     }

    # def _extract_bill_detail_fields(self, bill_data: Dict) -> Dict:
    #     """BillDetail 모델에 필요한 필드만 추출"""
    #     detail_fields = [
    #         "BILL_ID",
    #         "PROC_DT",
    #         "DETAIL_LINK",
    #         "LAW_SUBMIT_DT",
    #         "LAW_PRESENT_DT",
    #         "LAW_PROC_DT",
    #         "LAW_PROC_RESULT_CD",
    #         "COMMITTEE_DT",
    #         "CMT_PRESENT_DT",
    #         "CMT_PROC_DT",
    #         "CMT_PROC_RESULT_CD",
    #         "PROC_RESULT",
    #         "GVRN_TRSF_DT",
    #         "PROM_LAW_NM",
    #         "PROM_DT",
    #         "PROM_NO",
    #     ]

    #     return {
    #         field: bill_data.get(field) for field in detail_fields if field in bill_data
    #     }