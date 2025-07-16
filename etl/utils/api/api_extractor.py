import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm

from ...utils.file.fileio import write_file
from ..http.client import HTTPClient
from .api_schema import BaseAPI

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class APIExtractor:
    """API 데이터 추출기"""

    def __init__(
        self,
        api_client: BaseAPI,
        output_dir: str = "output",
        max_concurrent_requests: int = 10,
    ):
        self.api_client = api_client
        self.http_client = HTTPClient(max_concurrent_requests)
        self.output_dir = output_dir
        self.data = {}

        os.makedirs(self.output_dir, exist_ok=True)

    async def __aenter__(self):
        """Context manager 진입"""
        await self.http_client.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        await self.http_client.close_session()

    async def close(self):
        """수동으로 세션 종료"""
        await self.http_client.close_session()

    async def _get_total_count(self, api_name: str, url: str, **kwargs) -> int:
        """총 데이터 개수 확인"""
        params = kwargs.copy()
        params.update(
            {
                self.api_client.PAGE_NUM_PARAM: 1,
                self.api_client.PAGE_SIZE_PARAM: 1,
            }
        )
        result = await self.http_client.make_request(url, params)
        if result:
            return self.api_client.extract_total_count(api_name, result)
        return 0

    async def fetch_page_data(self, url: str, page: int, page_size: int = 100, **kwargs) -> list[dict]:
        """단일 페이지 데이터 가져오기"""
        params = kwargs.copy()
        params.update(
            {
                self.api_client.PAGE_NUM_PARAM: page,
                self.api_client.PAGE_SIZE_PARAM: page_size,
            }
        )
        result = await self.http_client.make_request(url, params)
        return result

    async def _get_request_var(self, api_name: str, **kwargs) -> tuple:
        url, params = self.api_client.build_url(api_name, **kwargs)
        return url, params

    async def extract(self, api_name: str, is_save: bool = True, **kwargs) -> list[dict]:
        """데이터 추출 메인 메서드"""
        url, params = await self._get_request_var(api_name, **kwargs)
        total_count = await self._get_total_count(api_name, url, **params)
        logger.info(f"{api_name}: 총 {total_count}개 항목 발견")

        if total_count == 0:
            return []

        # 필요한 페이지 수 계산
        page_size = 100
        total_pages = (total_count + page_size - 1) // page_size

        all_data = []
        for page in tqdm(range(1, total_pages + 1), desc="데이터 수집"):
            page_data = await self.fetch_page_data(url, page, page_size, **params)
            all_data.append(page_data)
        
        if is_save:
            return await self.save(api_name, all_data)

        self.data[api_name] = all_data
        return all_data

    async def extract_multiple(self, api_requests: dict[str, dict], is_save: bool = True) -> dict[str, list[dict]]:
        """여러 API 동시 추출"""
        tasks = [self.extract(api_name, is_save, **params) for api_name, params in api_requests.items()]
        results = await asyncio.gather(*tasks)
        return dict(zip(api_requests.keys(), results))

    async def save(self, api_name: str, data: list[dict]) -> str:
        if not data:
            logger.warning(f"{api_name}: 저장할 데이터가 없습니다.")
            return ""

        filepath = f"{self.output_dir}/{api_name}_{datetime.now().strftime('%Y-%m-%d')}.json"
        await write_file(filepath, data)
        return api_name, filepath
