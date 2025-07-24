import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass
class DownloadItem:
    """다운로드할 항목의 기본 정보"""
    url: str
    filename: str
    item_id: Optional[str] = None
    title: Optional[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DownloadResult:
    """다운로드 결과"""
    item: DownloadItem
    success: bool
    file_path: Optional[Path] = None
    error_msg: str = ""
    file_size: int = 0


@dataclass
class DownloadStats:
    """다운로드 통계"""
    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: float = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()

    @property
    def progress_pct(self) -> float:
        return (self.completed + self.failed + self.skipped) / self.total * 100 if self.total > 0 else 0

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time


@runtime_checkable
class InfoExtractorProtocol(Protocol):
    """정보 추출기 프로토콜"""

    async def convert_to_download_items(self, *args, **kwargs) -> list[DownloadItem]:
        """DownloadItem 리스트로 변환"""
        ...

    async def extract_download_info(self, *args, **kwargs) -> list[DownloadItem]:
        """다운로드 정보 추출 메서드"""
        ...

    async def extract_batch_info(self, items: list) -> list[DownloadItem]:
        """배치 단위로 여러 항목의 정보 추출"""
        ...


@runtime_checkable
class FileDownloaderProtocol(Protocol):
    """파일 다운로더 프로토콜"""

    async def download_file(self, item: DownloadItem, output_dir: str) -> DownloadResult:
        """단일 파일 다운로드"""
        ...

    async def download_batch(self, items: list[DownloadItem], output_dir: str) -> list[DownloadResult]:
        """배치 단위 파일 다운로드"""
        ...


@runtime_checkable
class FileDownloadProgressorProtocol(Protocol):
    """파일 다운로드 진행 프로세서 프로토콜"""
    
    async def download_all(self, source_path: str, output_dir: str) -> list[DownloadResult]:
        """전체 다운로드 프로세스 실행"""
        ...
