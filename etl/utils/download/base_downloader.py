import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import aiohttp

from ...utils.file.fileio import read_file
from .downloader import (
    DownloadItem,
    DownloadResult,
    DownloadStats,
    FileDownloaderProtocol,
    InfoExtractorProtocol,
)


class FileDownloader:
    def __init__(
        self,
        max_concurrent_downloads: int = 10,
        retry_attempts: int = 3,
        delay_between_requests: float = 0.5,
        headers: dict[str, str] = None
    ):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.retry_attempts = retry_attempts
        self.delay_between_requests = delay_between_requests
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
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
            headers=self.headers,
            timeout=self.timeout,
            connector=self.connector
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
        await self.connector.close()

    async def download_file(self, item: DownloadItem, output_dir: str) -> DownloadResult:
        """단일 파일 다운로드 (재시도 포함)"""
        file_path = Path(output_dir) / item.filename
        
        # 이미 존재하는 파일 체크
        if file_path.exists() and file_path.stat().st_size > 1024:
            self.logger.info(f"파일 존재로 건너뜀: {item.filename}")
            return DownloadResult(
                item=item,
                success=True,
                file_path=file_path,
                file_size=file_path.stat().st_size
            )

        for attempt in range(self.retry_attempts):
            try:
                result = await self._download_single_file(item, file_path)
                self.logger.info(f"다운로드 완료: {item.filename}")
                return result
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    self.logger.error(f"다운로드 최종 실패 {item.filename}: {e}")
                    return DownloadResult(
                        item=item,
                        success=False,
                        error_msg=str(e)
                    )
                await asyncio.sleep(1 * (attempt + 1))

    async def _download_single_file(self, item: DownloadItem, file_path: Path) -> DownloadResult:
        """실제 파일 다운로드 수행"""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with self.session.get(item.url) as response:
            response.raise_for_status()

            async with aiofiles.open(file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)

        file_size = file_path.stat().st_size
        return DownloadResult(
            item=item,
            success=True,
            file_path=file_path,
            file_size=file_size
        )

    async def download_batch(self, items: list[DownloadItem], output_dir: str) -> list[DownloadResult]:
        """배치 단위 파일 다운로드"""
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        
        async def download_with_semaphore(item: DownloadItem):
            async with semaphore:
                await asyncio.sleep(self.delay_between_requests)
                return await self.download_file(item, output_dir)

        tasks = [download_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(DownloadResult(
                    item=items[i],
                    success=False,
                    error_msg=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results

    @staticmethod
    def make_safe_filename(filename: str) -> str:
        """안전한 파일명 생성"""
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = re.sub(r"\s+", "_", filename)
        filename = filename.strip("_")

        if len(filename) > 100:
            filename = filename[:100]

        return filename or "unknown"


class InfoExtractor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def convert_to_download_items(self, item_cls) -> list[DownloadItem]:
        return [DownloadItem(
            item_id=item_cls.item_id or None,
            title=item_cls.title or None,
            url=item_cls.url,
            filename=item_cls.filename,
            metadata=item_cls.metadata or {}
        )]

    async def extract_download_info(self, item_cls) -> list[DownloadItem]:
        return self.convert_to_download_items(item_cls)

    async def extract_batch_info(self, items: list) -> list[DownloadItem]:
        semaphore = asyncio.Semaphore(10)

        async def extract_with_semaphore(item_cls):
            async with semaphore:
                return await self.extract_download_info(item_cls)

        tasks = [extract_with_semaphore(item_cls) for item_cls in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"정보 추출 실패: {result}")
            elif isinstance(result, list):
                all_items.extend(result)
        return all_items


class FileDownloadProgressor:
    def __init__(
        self,
        info_extractor,
        file_downloader,
        batch_size: int = 100
    ):
        self.info_extractor: InfoExtractorProtocol = info_extractor
        self.file_downloader: FileDownloaderProtocol = file_downloader
        self.batch_size = batch_size

        self.stats = DownloadStats()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.all_results: list[DownloadResult] = []

    async def download_all(self, source_path: str, output_dir: str) -> list[DownloadResult]:
        data_list = await read_file(source_path)
        self.stats.total = len(data_list)
        self.logger.info(f"대량 다운로드 시작: {len(data_list)}개 데이터")

        all_results = []
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(data_list) + self.batch_size - 1) // self.batch_size
            
            self.logger.info(f"배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개 항목)")
            
            try:
                batch_results = await self._process_batch(batch, output_dir)
                all_results.extend(batch_results)
                self._update_stats(batch_results)
                
                # 진행상황 로그
                if batch_num % 5 == 0:
                    self._log_progress()
                
                # 배치 간 휴식
                if i + self.batch_size < len(data_list):
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"배치 {batch_num} 처리 오류: {e}")
        
        await self._save_final_results(output_dir)
        self._log_progress()
        
        return all_results

    async def _process_batch(self, batch: list[tuple], output_dir: str) -> list[DownloadResult]:
        """배치 단위 처리"""
        download_items = await self.info_extractor.extract_batch_info(batch)
        results = await self.file_downloader.download_batch(download_items, output_dir)
        return results

    def _update_stats(self, results: list[DownloadResult]):
        """통계 업데이트"""
        for result in results:
            if result.success:
                if result.file_path and result.file_path.exists():
                    self.stats.completed += 1
                else:
                    self.stats.skipped += 1
            else:
                self.stats.failed += 1

    def _log_progress(self):
        """진행상황 로그"""
        elapsed = self.stats.elapsed_time
        rate = self.stats.completed / elapsed if elapsed > 0 else 0
        eta = (self.stats.total - self.stats.completed - self.stats.failed - self.stats.skipped) / rate if rate > 0 else 0

        self.logger.info(
            f"진행: {self.stats.completed}/{self.stats.total} "
            f"({self.stats.progress_pct:.1f}%) "
            f"실패: {self.stats.failed}, 건너뜀: {self.stats.skipped} "
            f"속도: {rate:.1f}/sec, ETA: {eta:.0f}초"
        )

    async def _save_final_results(self, output_dir: str):
        """최종 결과 저장"""
        # 결과 요약 저장
        summary = {
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "total": self.stats.total,
                "completed": self.stats.completed,
                "failed": self.stats.failed,
                "skipped": self.stats.skipped,
                "elapsed_time": self.stats.elapsed_time,
                "success_rate": self.stats.completed / self.stats.total if self.stats.total > 0 else 0
            },
            "results": [
                {
                    "item_id": result.item.item_id,
                    "title": result.item.title,
                    "success": result.success,
                    "file_path": str(result.file_path) if result.file_path else None,
                    "file_size": result.file_size,
                    "error_msg": result.error_msg
                }
                for result in self.all_results
            ]
        }
        
        summary_file = Path(output_dir) / "download_summary.json"
        async with aiofiles.open(summary_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(summary, ensure_ascii=False, indent=2))
        
        self.logger.info(f"다운로드 요약 저장: {summary_file}")
