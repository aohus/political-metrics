import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

from ...utils.download.base_downloader import DownloadItem


@dataclass
class DocumentInfo:
    bill_id: str
    title: str = ""
    bill_links: list[dict[str, str]] = field(default_factory=list)
    conf_links: list[dict[str, str]] = field(default_factory=list)
    status: str = "pending"
    error_msg: str = ""


class DocumentInfoExtractor:
    """국회 의안정보시스템 정보 추출기"""
    
    def __init__(
        self,
        max_concurrent_info_fetch: int = 20,
        delay_between_requests: float = 0.5
    ):
        self.base_url = "https://likms.assembly.go.kr/bill/billDetail.do?billId="
        self.max_concurrent_info_fetch = max_concurrent_info_fetch
        self.delay_between_requests = delay_between_requests
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 시작"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=timeout,
            connector=connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    async def extract_download_info(self, bill_id: str, title: str) -> list[DownloadItem]:
        """단일 의안의 다운로드 정보 추출"""
        bill_info = await self._get_bill_info_with_retry(bill_id, title)
        return self.convert_to_download_items(bill_info)

    async def extract_batch_info(self, items: list[tuple]) -> list[DownloadItem]:
        """배치 단위로 의안 정보 추출"""
        semaphore = asyncio.Semaphore(self.max_concurrent_info_fetch)

        async def extract_with_semaphore(bill_id: str, title: str):
            async with semaphore:
                await asyncio.sleep(self.delay_between_requests)
                return await self.extract_download_info(bill_id, title)

        tasks = [extract_with_semaphore(bill_id, title) for bill_id, title in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"정보 추출 실패: {result}")
            elif isinstance(result, list):
                all_items.extend(result)
        return all_items

    async def _get_bill_info_with_retry(self, bill_id: str, title: str, retry_attempts: int = 3) -> DocumentInfo:
        """재시도 로직이 포함된 의안 정보 추출"""
        bill_url = self.base_url + bill_id

        for attempt in range(retry_attempts):
            try:
                return await self._get_bill_info_single(bill_url, bill_id, title)
            except Exception as e:
                if attempt == retry_attempts - 1:
                    self.logger.error(f"의안 정보 추출 최종 실패 {bill_id}: {e}")
                    return DocumentInfo(
                        bill_id=bill_id,
                        title=title,
                        status="failed",
                        error_msg=str(e),
                    )
                await asyncio.sleep(2 ** attempt)

    async def _get_bill_info_single(self, bill_url: str, bill_id: str, title: str) -> DocumentInfo:
        """단일 의안 정보 추출"""
        bill_info = DocumentInfo(bill_id=bill_id, title=title, status="processing")

        async with self.session.get(bill_url) as response:
            response.raise_for_status()
            html_content = await response.text()

        bill_info.bill_links, bill_info.conf_links = self._extract_pdf_links(html_content)
        bill_info.status = "completed"
        return bill_info

    def _extract_pdf_links(self, html_content: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """HTML에서 PDF 링크 추출"""
        bill_links = []
        conf_links = []
        link_map = set()

        # JavaScript FileGate 링크 패턴
        js_bill_pattern = r"javascript:openBillFile\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
        js_matches = re.findall(js_bill_pattern, html_content, re.IGNORECASE)

        for i, match in enumerate(js_matches):
            if len(match) >= 2:
                base_url = match[0]
                book_id = match[1]
                if book_id in link_map:
                    continue

                link_map.add(book_id)
                download_url = f"{base_url}?bookId={book_id}&type=1"

                bill_links.append({
                    "url": download_url,
                    "title": "의안원문" if i == 0 else "보고서",
                    "file_id": book_id,
                    "base_url": base_url,
                })

        # 회의록 링크 패턴
        js_conf_pattern = r"javascript:openConfFile\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
        js_matches = re.findall(js_conf_pattern, html_content, re.IGNORECASE)

        for match in js_matches:
            if len(match) >= 2:
                base_url = match[0]
                path = match[1]
                download_url = f"{base_url}pdf.do?confernum={path}&type=1"

                conf_links.append({
                    "url": download_url,
                    "title": "회의록",
                    "file_id": path,
                    "base_url": base_url,
                })

        return bill_links, conf_links

    def convert_to_download_items(self, bill_info: DocumentInfo) -> list[DownloadItem]:
        """DocumentInfo를 DownloadItem 리스트로 변환"""
        items = []

        # 의안원문만 다운로드 (필요시 다른 문서도 추가 가능)
        for link in bill_info.bill_links:
            if link["title"] == "의안원문":
                filename = f"{bill_info.title}.pdf"

                item = DownloadItem(
                    item_id=bill_info.bill_id,
                    title=bill_info.title,
                    url=link["url"],
                    filename=filename,
                    metadata={
                        "bill_info": bill_info,
                        "link_info": link,
                        "document_type": "bill"
                    }
                )
                items.append(item)
                break  # 의안원문 하나만 다운로드
        return items
