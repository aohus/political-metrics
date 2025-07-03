import asyncio
import json
import os

from assembly.api_metadata import AssemblyAPI
from utils.extract.api import APIExtractor

from .bill_processor import BillProcessor, BillProposerProcessor


async def main():
    raw_data_dir = "./data/assembly/temp/raw/"
    formatted_data_dir = "./data/assembly/temp/formatted/"

    api_client = AssemblyAPI()
    try:
        async with APIExtractor(api_client, raw_data_dir) as extractor:
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
    for fname in os.listdir(raw_data_dir):
        path_list.append((fname.split(".")[0], raw_data_dir+fname))

    with open(raw_data_dir+"bills.json", "r") as f:
        bills = json.load(f)

    bill_processor = BillProcessor(formatted_data_dir)
    bill_proposer_processor = BillProposerProcessor(formatted_data_dir, default_age="22")

    tasks = [bill_processor.process(path_list), bill_proposer_processor.process_bill_proposers(bills)]
    results = asyncio.gather(*tasks, return_exceptions=True)

    bill_result, bill_processor_result = results
    for table_name, data in bill_result.items:
        with open(formatted_data_dir+table_name+".json", "w", encoding='utf-8', indent=2) as f:
            json.dump(f, data)

    with open(formatted_data_dir+"proposer_bill.json", "w", encoding='utf-8', indent=2) as f:
        json.dump(f, bill_processor_result)
    # UpsertDBProcessor.process(formatted_data_dir)
    # CleanDirProcessor.process()