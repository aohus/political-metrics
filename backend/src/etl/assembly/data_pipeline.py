import asyncio
import json
import os

from ..utils.extract.api import APIExtractor
from .api_metadata import AssemblyAPI
from .bill_processor import BillProcessor, BillProposerProcessor


async def main():
    raw_data_dir = "./data/assembly/temp/raw/"
    formatted_data_dir = "./data/assembly/temp/formatted/"

    # api_client = AssemblyAPI()
    # try:
    #     async with APIExtractor(api_client, raw_data_dir) as extractor:
    #         # 여러 API 동시 추출
    #         multiple_requests = {
    #             "bills": {},
    #         }
    #         results = await extractor.extract_multiple(multiple_requests)
    #         for api_name, data in results.items():
    #             extractor.save_to_json(api_name, data)
    # except Exception as e:
    #     print(f"오류 발생: {e}")
    # finally:
    #     print("모든 세션이 정리되었습니다.")

    # path_list = []
    # for fname in os.listdir(raw_data_dir):
    #     path_list.append((fname.split(".")[0], raw_data_dir+fname))

    # with open(raw_data_dir+"bills.json", "r") as f:
    #     bills = json.load(f)

    base_dir = "/Users/aohus/Workspaces/github/politics/backend/src/etl/data/assembly"
    path_list = [
        ("law_bills_member", f"{base_dir}/raw/bills.json"),
        ("law_bills_gov", f"{base_dir}/raw/law_bill_all.json"),
    ]
    with open(f"{base_dir}/raw/bills.json", "r") as f:
        bills = json.load(f)

    bill_processor = BillProcessor(formatted_data_dir)
    bill_proposer_processor = BillProposerProcessor(default_age="22")

    tasks = [
        bill_processor.process(path_list),
        bill_proposer_processor.process_bill_proposers(bills),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    (bill, bill_detail), bill_processor_result = results
    for table_name, data in (bill, bill_detail):
        with open(
            "/Users/aohus/Workspaces/github/politics/backend/src/etl/data/assembly/temp/"
            + table_name
            + ".json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(data, f, indent=2)
    
    with open(
        "/Users/aohus/Workspaces/github/politics/backend/src/etl/data/assembly/temp/"
        + "proposer_bill.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(results, f, indent=2)
    # UpsertDBProcessor.process(formatted_data_dir)
    # CleanDirProcessor.process()

asyncio.run(main())
