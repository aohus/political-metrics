import asyncio
import json
import logging
from typing import Dict, List, Tuple

import pandas as pd
from api.model.orm import Bill, BillDetail, BillProposer
from core.schema.utils import BillStatus, ProposerType

from ...utils.date import DateConverter
from ...utils.file import read_file, write_file

logger = logging.getLogger(__name__)


class BillProcessor:
    def __init__(self, config):
        self.date_converter = DateConverter()
        self.output_dir = config.assembly_temp_raw
        self._load_alter_bill_link(config.alter_bill_link)

    def _load_alter_bill_link(self, alter_bill_link: str) -> None:
        if not self.alter_bill_link:
            alter_bill_link = self.output_dir / "alter_bill_link.json"
        with open(alter_bill_link, "r", encoding="utf-8") as f:
            self.alter_bill_link = json.load(f)

    async def process(self, path_list: list, is_save: bool = True) -> Tuple[List[Dict], List[Dict]]:
        tasks = [self.transform(api_name, path) for api_name, path in path_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        merged_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(str(result))
                raise result
            else:
                merged_results.extend(result)
        merged_results = await self.convert_to_table_format(merged_results, is_save=is_save)
        return merged_results

    async def transform(self, api_name: str, path: str) -> None:
        data = await read_file(path)
        handlers = {
            "law_bill_member": self._transform_member_bills,
            "law_bill_gov": self._transform_government_bills,
            "law_bill_cap": self._transform_government_bills,
        }
        if handler := handlers.get(api_name):
            try:
                result = await handler(data)
                logger.info(f"Successfully transformed {api_name} data from {path}")
                return result
            except Exception as e:
                logger.error(f"Failed to transform {api_name}: {e}")
                raise e
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
        df = df[(df["PROPOSER_KIND"] != "의원")]
        df["PROPOSER_KIND"] = df["PROPOSER_KIND"].apply(
            lambda x: ProposerType.GOVERNMENT if x == "정부" else ProposerType.COMMITTEE
        )
        df["PUBL_PROPOSER"] = None
        df["MEMBER_LIST"] = None
        df = df.drop(columns=["COMMITTEE_PROC_DT", "RST_MONA_CD"], errors="ignore")
        return df.to_dict(orient="records")

    async def convert_to_table_format(self, bills: list, is_save: bool = True) -> Tuple[List[Dict], List[Dict]]:
        bill_list, bill_detail_list = [], []
        try:
            for bill in bills:
                bill["COMMITTEE_NAME"] = bill.get("COMMITTEE")
                bill["STATUS"] = self._determine_bill_status(bill)
                if bill["STATUS"] in [BillStatus.AMENDED_DISCARDED, BillStatus.ALTERNATIVE_DISCARDED]:
                    alter_no = self._link_alter_bill_no(bill["BILL_NO"])
                    bill["ALTER_BILL_NO"] = alter_no
                bill_list.append({field: bill.get(field, None) for field in Bill.__table__.columns.keys()})
                bill_detail_list.append({field: bill.get(field, None) for field in BillDetail.__table__.columns.keys()})
        except Exception as e:
            logger.error(e, exc_info=True)
        
        if is_save:
            await self.save(bill_list, bill_detail_list)
        return ("bills", bill_list), ("bill_details", bill_detail_list)

    async def save(self, bills: List[Dict], bill_details: List[Dict]) -> None:
        """Save bills and bill details to JSON files"""
        try:
            tasks = [
                write_file(self.output_dir / "bills.json", bills),
                write_file(self.output_dir / "bill_details.json", bill_details)
            ]
            asyncio.run(asyncio.gather(*tasks))
        except Exception as e:
            logger.error(f"Failed to save bills: {e}", exc_info=True)

    def _link_alter_bill_no(self, bill_no: str) -> list:
        try:
            if len(bill_no) <= 5:
                bill_no = "22" + bill_no.zfill(5)
            return self.alter_bill_link[bill_no]
        except:
            logger.error(f"Fail to find alternative bill number: {bill_no}")
            return None

    def _determine_bill_status(self, bill_data: Dict) -> str:
        """의안 상태 결정"""
        try:
            # 위원회가 지정되지 않은 경우
            if not bill_data.get("COMMITTEE"):
                return BillStatus.WAITING
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
            process_stages = {field: bill_data[field] for field in status_fields if bill_data.get(field) is not None}

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


async def process_bills(config, data_paths, output_dir: str):
    assembly_ref = config.assembly_ref
    alter_bill_link = await read_file(assembly_ref / "alter_bill_link.json")

    bill_processor = BillProcessor(alter_bill_link, output_dir)  # TODO: remove alter_bill_link
    bills, bill_details = await bill_processor.process(data_paths)

    for table_name, data in (bills, bill_details):
        filepath = output_dir / f"{table_name}.json"
        await write_file(filepath, data)
