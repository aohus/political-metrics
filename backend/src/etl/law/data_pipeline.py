from .api_metadata import LawAPI
from ..utils.extract.api import APIExtractor

# processing
# save


async def run():
    api_client = LawAPI()
    try:
        async with APIExtractor(api_client, "./law_api/data") as law_extractor:
            # 여러 API 동시 추출
            multiple_requests = {
                "cur_law": {},
                "cur_admrul": {},
                "cur_ordin": {},
                "cur_trty": {},
            }
            results = await law_extractor.extract_multiple(multiple_requests)
            for api_name, data in results.items():
                law_extractor.save_to_json(api_name, data)
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        print("모든 세션이 정리되었습니다.")


