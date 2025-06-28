import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import parse_qs, urlparse

import aiofiles
import aiohttp


@dataclass
class BillInfo:
    """의안 정보"""

    bill_id: str
    title: str = ""
    bill_links: List[Dict[str, str]] = field(default_factory=list)
    conf_links: List[Dict[str, str]] = field(default_factory=list)
    status: str = "pending"  # pending, processing, completed, failed
    error_msg: str = ""


@dataclass
class DownloadStats:
    """다운로드 통계"""

    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def progress_pct(self) -> float:
        return (
            (self.completed + self.failed + self.skipped) / self.total * 100
            if self.total > 0
            else 0
        )

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time


class MassAssemblyPDFDownloader:
    """대용량 국회 의안정보시스템 비동기 PDF 다운로더"""

    def __init__(
        self,
        max_concurrent_downloads: int = 10,
        max_concurrent_info_fetch: int = 20,
        batch_size: int = 100,
        retry_attempts: int = 3,
        delay_between_requests: float = 0.5,
    ):

        self.base_url = "https://likms.assembly.go.kr/bill/billDetail.do?billId="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
        }

        # 동시성 제어
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_concurrent_info_fetch = max_concurrent_info_fetch
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.delay_between_requests = delay_between_requests

        # 상태 관리
        self.all_bill_infos: List[BillInfo] = []
        self.downloaded_files: Set[str] = set()
        self.stats = DownloadStats()
        self.logger = logging.getLogger(__name__)

        # 세션 설정
        self.connector = aiohttp.TCPConnector(
            limit=200,
            limit_per_host=50,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        self.timeout = aiohttp.ClientTimeout(total=60, connect=10)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 시작"""
        self.session = aiohttp.ClientSession(
            headers=self.headers, timeout=self.timeout, connector=self.connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.session.close()
        await self.connector.close()

    def extract_bill_id_from_url(self, url: str) -> Optional[str]:
        """URL에서 billId 추출"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            return query_params.get("billId", [None])[0]
        except Exception as e:
            self.logger.error(f"URL 파싱 오류: {e}")
            return None

    async def get_bill_info_with_retry(self, bill_id: str, bill_title: str) -> BillInfo:
        """재시도 로직이 포함된 의안 정보 추출"""
        bill_url = self.base_url + bill_id

        for attempt in range(self.retry_attempts):
            try:
                return await self._get_bill_info_single(bill_url, bill_id, bill_title)
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    self.logger.error(f"의안 정보 추출 최종 실패 {bill_id}: {e}")
                    bill_info = BillInfo(
                        bill_id=bill_id,
                        title=bill_title,
                        status="failed",
                        error_msg=str(e),
                    )
                    return bill_info
                await asyncio.sleep(2**attempt)  # 지수 백오프

    async def _get_bill_info_single(
        self, bill_url: str, bill_id: str, bill_title: str
    ) -> BillInfo:
        """단일 의안 정보 추출"""
        bill_info = BillInfo(bill_id=bill_id, title=bill_title, status="processing")

        async with self.session.get(bill_url) as response:
            response.raise_for_status()
            html_content = await response.text()

        bill_info.bill_links, bill_info.conf_links = self._extract_pdf_links(
            html_content
        )
        bill_info.status = "completed"
        return bill_info

    def _extract_pdf_links(
        self, html_content: str
    ) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """PDF 링크 추출"""
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

                bill_links.append(
                    {
                        "url": download_url,
                        "title": "의안원문" if i == 0 else "보고서",
                        "file_id": book_id,
                        "base_url": base_url,
                    }
                )

        # 회의록 링크 패턴
        js_conf_pattern = (
            r"javascript:openConfFile\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
        )
        js_matches = re.findall(js_conf_pattern, html_content, re.IGNORECASE)

        for match in js_matches:
            if len(match) >= 2:
                base_url = match[0]
                path = match[1]
                download_url = f"{base_url}pdf.do?confernum={path}&type=1"

                conf_links.append(
                    {
                        "url": download_url,
                        "title": "회의록",
                        "file_id": path,
                        "base_url": base_url,
                    }
                )

        return bill_links, conf_links

    async def download_pdf_with_retry(
        self, bill_info: BillInfo, output_dir: str
    ) -> Optional[Path]:
        """재시도 로직이 포함된 PDF 다운로드"""
        if not bill_info.bill_links:
            return None

        # 의안원문만 다운로드
        pdf_link = None
        for link in bill_info.bill_links:
            if link["title"] == "의안원문":
                pdf_link = link
                break

        if not pdf_link:
            return None

        filename = self._make_safe_filename(bill_info.title)
        file_path = Path(output_dir) / f"{filename}.pdf"

        # 이미 다운로드된 파일 체크
        if file_path.exists() and file_path.stat().st_size > 1024:
            self.stats.skipped += 1
            return file_path

        for attempt in range(self.retry_attempts):
            try:
                return await self._download_pdf_single(pdf_link["url"], file_path)
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    self.logger.error(f"PDF 다운로드 최종 실패 {bill_info.title}: {e}")
                    self.stats.failed += 1
                    return None
                await asyncio.sleep(1 * (attempt + 1))

    async def _download_pdf_single(self, pdf_url: str, file_path: Path) -> Path:
        """단일 PDF 다운로드"""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with self.session.get(pdf_url) as response:
            response.raise_for_status()

            # Content-Type 체크
            # content_type = response.headers.get("content-type", "").lower()
            # if (
            #     "pdf" not in content_type
            #     and "application/octet-stream" not in content_type
            # ):
            #     raise Exception(f"잘못된 Content-Type: {content_type}")

            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)

        # 파일 크기 검증
        # file_size = file_path.stat().st_size
        # if file_size < 1024:
        #     raise Exception("파일이 너무 작습니다 (오류 페이지일 가능성)")

        self.stats.completed += 1
        return file_path

    async def process_bill_batch(
        self,
        bill_batch: List[tuple],
        output_dir: str,
        info_semaphore: asyncio.Semaphore,
        download_semaphore: asyncio.Semaphore,
    ) -> List[Path]:
        """배치 단위 처리"""
        # 1단계: 의안 정보 수집
        info_tasks = []
        for bill_id, bill_title in bill_batch:

            async def get_info_with_semaphore(bid, btitle):
                async with info_semaphore:
                    await asyncio.sleep(self.delay_between_requests)
                    return await self.get_bill_info_with_retry(bid, btitle)

            info_tasks.append(get_info_with_semaphore(bill_id, bill_title))

        bill_infos = await asyncio.gather(*info_tasks, return_exceptions=True)
        valid_bill_infos = [
            bi
            for bi in bill_infos
            if isinstance(bi, BillInfo) and bi.status == "completed"
        ]

        # 2단계: PDF 다운로드
        download_tasks = []
        for bill_info in valid_bill_infos:

            async def download_with_semaphore(bi):
                async with download_semaphore:
                    await asyncio.sleep(self.delay_between_requests)
                    return await self.download_pdf_with_retry(bi, output_dir)

            download_tasks.append(download_with_semaphore(bill_info))

        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        downloaded_files = [result for result in results if isinstance(result, Path)]

        # 배치별 bill_info 저장
        self.all_bill_infos.extend(valid_bill_infos)
        return downloaded_files

    def _log_progress(self):
        """진행상황 로그"""
        elapsed = self.stats.elapsed_time
        rate = self.stats.completed / elapsed if elapsed > 0 else 0
        eta = (
            (
                self.stats.total
                - self.stats.completed
                - self.stats.failed
                - self.stats.skipped
            )
            / rate
            if rate > 0
            else 0
        )

        self.logger.info(
            f"진행: {self.stats.completed}/{self.stats.total} "
            f"({self.stats.progress_pct:.1f}%) "
            f"실패: {self.stats.failed}, 건너뜀: {self.stats.skipped} "
            f"속도: {rate:.1f}/sec, ETA: {eta:.0f}초"
        )

    def _get_new_bill_list(path: str):
        with open(path, "r") as f:
            bills = json.load(f)

        return [
            (bill["BILL_ID"], f"{bill["BILL_NO"]}_{bill["BILL_NAME"]}")
            for bill in bills
        ]

    async def download_mass_bills(
        self, path: str, output_dir: str = "./billsPDF"
    ) -> List[Path]:

        bill_list = self._get_new_bill_list(path)

        """대량 의안 문서 다운로드"""
        self.stats.total = len(bill_list)
        self.stats.start_time = time.time()

        self.logger.info(f"대량 다운로드 시작: {len(bill_list)}개 의안")

        # 출력 디렉토리 생성
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 세마포어 생성
        info_semaphore = asyncio.Semaphore(self.max_concurrent_info_fetch)
        download_semaphore = asyncio.Semaphore(self.max_concurrent_downloads)

        all_downloaded_files = []

        # 배치 단위로 처리
        for i in range(0, len(bill_list), self.batch_size):
            batch = bill_list[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(bill_list) + self.batch_size - 1) // self.batch_size

            self.logger.info(
                f"배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개 의안)"
            )

            try:
                downloaded_files = await self.process_bill_batch(
                    batch, output_dir, info_semaphore, download_semaphore
                )
                all_downloaded_files.extend(downloaded_files)

                # 진행상황 로그
                if batch_num % 5 == 0:  # 5배치마다 로그
                    self._log_progress()

                # 배치 간 휴식
                if i + self.batch_size < len(bill_list):
                    await asyncio.sleep(2)

            except Exception as e:
                self.logger.error(f"배치 {batch_num} 처리 오류: {e}")

        # 최종 결과
        self._log_progress()
        self.logger.info(f"전체 다운로드 완료: {len(all_downloaded_files)}개 파일")

        final_info_file = f"{output_dir}/all_bill_infos.json"
        await self.save_bill_infos(self.all_bill_infos, final_info_file)
        self.logger.info(f"의안 정보 저장 완료: {final_info_file}")

        return all_downloaded_files

    def _make_safe_filename(self, filename: str) -> str:
        """안전한 파일명 생성"""
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = re.sub(r"\s+", "_", filename)
        filename = filename.strip("_")

        if len(filename) > 100:
            filename = filename[:100]

        return filename or "unknown"

    async def save_bill_infos(self, bill_infos: List[BillInfo], output_file: str):
        """의안 정보를 JSON 파일로 저장"""
        import json
        from datetime import datetime

        data = {
            "timestamp": datetime.now().isoformat(),
            "total_count": len(bill_infos),
            "bills": [
                {
                    "bill_id": bi.bill_id,
                    "title": bi.title,
                    "status": bi.status,
                    "bill_links_count": len(bi.bill_links),
                    "conf_links_count": len(bi.conf_links),
                    "bill_links": bi.bill_links,
                    "conf_links": bi.conf_links,
                    "error_msg": bi.error_msg,
                }
                for bi in bill_infos
            ],
        }

        async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))


async def download_mass_assembly_pdfs(
    path: str,
    output_dir: str = "./billsPDF",
    max_concurrent_downloads: int = 10,
    max_concurrent_info_fetch: int = 20,
    batch_size: int = 100,
) -> List[Path]:
    """대량 PDF 다운로드 편의 함수"""

    async with MassAssemblyPDFDownloader(
        max_concurrent_downloads=max_concurrent_downloads,
        max_concurrent_info_fetch=max_concurrent_info_fetch,
        batch_size=batch_size,
    ) as downloader:
        return await downloader.download_mass_bills(path, output_dir)


async def main():
    """메인 실행 함수"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("download.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # 테스트용으로 작은 리스트 사용
    print(f"🔍 대용량 국회 의안정보시스템 PDF 다운로더")
    print("=" * 60)

    try:
        downloaded_files = await download_mass_assembly_pdfs(
            "path",
            output_dir="./mass_bills_pdf",
            max_concurrent_downloads=15,  # 동시 다운로드 수
            max_concurrent_info_fetch=25,  # 동시 정보 수집 수
            batch_size=50,  # 배치 크기
        )

        print(f"\n✅ 전체 다운로드 완료!")
        print(f"📁 다운로드된 파일: {len(downloaded_files)}개")
        print(f"💾 저장 위치: ./mass_bills_pdf/")

    except Exception as e:
        print(f"❌ 전체 프로세스 오류: {e}")


if __name__ == "__main__":
    # 필요한 패키지: pip install aiohttp aiofiles
    asyncio.run(main())
