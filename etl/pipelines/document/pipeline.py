import os
import time
from datetime import datetime

from utils.file.write_file import create_saver

from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import ExtractorProtocol, ProcessorProtocol, SaverProtocol

# Import necessary components
from .document_extractor import DocumentExtractor
from .document_parser import DocumentParser
from .pdf_processor import PDFProcessor


class DocumentPipeline(BasePipelineImpl):
    def __init__(self, config: any):
        super().__init__(config, "DocumentPipeline")
        self.extractor: ExtractorProtocol = DocumentExtractor()
        self.processor: ProcessorProtocol = PDFProcessor()

    async def _execute_pipeline(self, task_id: int, **kwargs) -> dict[str, any]:
        """Execute the document processing pipeline"""
        new_bill_path = self._get_new_bill_path(task_id)

        pdf_results = await self.stage_processor.execute_stage(
            "PDF Extraction",
            self.extractor.extract,
            new_bill_path,
            self.config.document_pdf
        )

        await self.stage_processor.execute_stage(
            "PDF Processing",
            self.processor.process,
            self.config.document_pdf
        )

        saver = create_saver(output_dir=self.config.document_parsed)
        parser = DocumentParser(saver)
        parse_results = await self.stage_processor.execute_stage(
            "Document Parsing",
            parser.parse,
            self.config.document_text
        )

        return {
            "task_id": task_id,
            "process_id": os.getpid(),
            "result": {
                "pdf_results": pdf_results,
                "parse_results": parse_results,
            },
            "kwargs": kwargs,
            "timestamp": time.time()
        }

    def _get_new_bill_path(self, i: int) -> str:
        """Generate path for new bill file"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.config.assembly_ref / f"new_bill_{date_str}_{i}.json"
