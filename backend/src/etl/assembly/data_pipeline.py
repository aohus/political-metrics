import asyncio
import json
import os

from ..utils.extract.api import APIExtractor
from .api_metadata import AssemblyAPI
from .bill_processor import BillProcessor, BillProposerProcessor


async def run(config):
    assembly_temp_raw = config.assembly_temp_raw
    assembly_temp_formatted = config.assembly_temp_formatted

    api_client = AssemblyAPI()
    try:
        async with APIExtractor(api_client, assembly_temp_raw) as extractor:
            # 여러 API 동시 추출
            multiple_requests = {
                "bills": {},
            }
            results = await extractor.extract_multiple(multiple_requests)
            for api_name, data in results.items():
                extractor.save_to_json(api_name, data)
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        print("모든 세션이 정리되었습니다.")

    path_list = []
    for fname in os.listdir(assembly_temp_raw):
        path_list.append((fname.split(".")[0], assembly_temp_raw / fname))

    with open(assembly_temp_raw / "bills.json", "r") as f:
        bills = json.load(f)

    with open(os.path.join(config.assembly_ref, "alter_bill_link.json"), "r", encoding="utf-8") as f:
        alter_bill_link = json.load(f)

    path_list = [
        ("law_bills_member", assembly_temp_raw / "bills.json"),
        ("law_bills_gov", assembly_temp_raw / "law_bill_all.json"),
    ]
    with open(assembly_temp_raw / "bills.json", "r") as f:
        bills = json.load(f)

    bill_processor = BillProcessor(assembly_temp_formatted)
    bill_proposer_processor = BillProposerProcessor(default_age="22")

    tasks = [
        bill_processor.process(path_list),
        bill_proposer_processor.process_bill_proposers(bills),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    (bill, bill_detail), bill_processor_result = results

    for table_name, data in (bill, bill_detail):
        with open(assembly_temp_formatted / f"{table_name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    with open(assembly_temp_formatted / "proposer_bill.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # UpsertDBProcessor.process(assembly_temp_formatted)
    # CleanDirProcessor.process()

