from datetime import datetime
from typing import Any, Optional

from ...utils.file.write_file import create_saver
from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import ExtractorProtocol, ProcessorProtocol, SaverProtocol
from .doc_downloader import DocumentExtractor
from .doc_parser import DocumentParser
from .pdf_processor import PDFProcessor


class DocumentPipeline(BasePipelineImpl):
    def __init__(self, config: Any):
        super().__init__(config, "DocumentPipeline")
        self.extractor: ExtractorProtocol = DocumentExtractor()
        self.pdf_processor: ProcessorProtocol = PDFProcessor()

    async def _execute_pipeline(self, **kwargs) -> dict[str, Any]:
        """Execute the document processing pipeline"""
        new_bill_path = self._get_new_bill_path()

        pdf_results = await self.stage_processor.execute_stage(
            "PDF Extraction",
            self.extractor.extract,
            new_bill_path,
            self.config.document_pdf
        )

        await self.stage_processor.execute_stage(
            "PDF Processing",
            self.pdf_processor.process,
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
            "pdf_results": pdf_results,
            "parse_results": parse_results,
            "new_bill_path": str(new_bill_path),
            "status": "completed"
        }

    def _get_new_bill_path(self) -> str:
        """Generate path for new bill file"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.config.assembly_ref / f"new_bill_{date_str}.json"
