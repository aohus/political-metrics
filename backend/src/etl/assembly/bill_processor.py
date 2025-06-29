import asyncio

from assembly.api_metadata import AssemblyAPI
from utils.extract.api import APIExtractor


class BillProcessor:
    def process(self, path: str):
        pass


async def main():
    api_client = AssemblyAPI()
    try:
        async with APIExtractor(api_client, "./assembly/data") as extractor:
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

    BillProcessor.process(path)

    rebuild_table(table_name, data)
    rebuild_table(table_name, query)
