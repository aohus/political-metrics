from ...utils.extract.api import APIExtractor
from .api_metadata import AssemblyAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def extract(request_apis: list, output_dir: str):
    api_client = AssemblyAPI()
    try:
        async with APIExtractor(api_client, output_dir) as extractor:
            # 여러 API 동시 추출
            multiple_requests = {api_name: dict() for api_name in request_apis}
            results = await extractor.extract_multiple(multiple_requests, is_save=True)
            return results
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        print("모든 세션이 정리되었습니다.")
