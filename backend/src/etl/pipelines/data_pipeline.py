from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Generic, Optional, Protocol, TypeVar, runtime_checkable

ResultT = TypeVar("ResultT")
T = TypeVar("T")
U = TypeVar("U")


class Extractor(Protocol[T]):
    def extract(self) -> T: ...


class Processor(Protocol[T, U]):
    def process(self, data: T) -> U: ...


class Saver(Protocol[T]):
    def save(self, data: T) -> None: ...


class DataPipeline(Generic[T, U]):
    def __init__(
        self,
        extractor: Extractor[T],
        processor: Processor[T, U],
        saver: Saver[U],
    ):
        self.extractor = extractor
        self.processor = processor
        self.saver = saver

    def run(self) -> None:
        path = self.extractor.extract()
        processed_path = self.processor.process(path)
        self.saver.save(processed_path)

    def update(self, data: T) -> None:
        """데이터 업데이트"""
        ...

    def process(self, data: T) -> ResultT:
        """데이터 처리"""
        ...

    def save(self, data: T) -> None:
        """데이터 저장"""
        ...


@dataclass
class ExtractorConfig:
    batch_size: int = 100
    timeout: float = 30.0
    retry_count: int = 3
    debug: bool = False


@dataclass
class ProcessorConfig:
    batch_size: int = 100
    timeout: float = 30.0
    retry_count: int = 3
    debug: bool = False


@dataclass
class SaverConfig:
    output_path: Path = field(default_factory=lambda: Path("./output"))
    format: str = "json"
    compression: bool = False
    backup: bool = True


class PipelineFactory:
    extractors = {
        "assembly_api": AssemblyAPIExtractor,
        "db": DatabaseExtractor,
        "file": FileExtractor,
    }
    processors = {
        "pdf": PDFProcessor,
        "bill_data": BillProcessor,
    }
    savers = {
        "db": DatabaseSaver,
        "file": FileSaver,
    }

    @classmethod
    def create_pipeline(cls, config: dict) -> DataPipeline:
        extractor = cls.extractors[config["source"]]()
        processor = cls.processors[config["format"]]()
        saver = cls.savers[config["target"]]()

        return DataPipeline(extractor, processor, saver)


# bill
bill_api_config = {
    "source": "assembly_api",
    "format": "bill_data",
    "saver": "db",
}
bill_api_pipeline = PipelineFactory.create_pipeline(bill_api_config)
bill_api_pipeline.run()


# bill
# update_db
# collector(api_info) -> data
# processor(data) -> bill, details, proposers
# save([])

# bill_pdf
bill_document_config = {
    "source": "file",
    "format": "pdf",
    "saver": "db",
}
bill_document_pipeline = PipelineFactory.create_pipeline(bill_document_config)
bill_document_pipeline.run()

# update
# collector(path) get_bill_ids -> bill_id list
# pdf_processor(bill_id list) * 5
# - pdf_downloader(bill_id list) -> output file path
# - pdf_extractor(file path) -> text
# - info_extractor(text) -> BillInfo
# - save(bill_info)
