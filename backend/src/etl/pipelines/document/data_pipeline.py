from datetime import datetime
from typing import Any, Optional

from ...utils.extract.download_file import download_mass_assembly_pdfs
from ...utils.processor.pdf_reader import extract_multiple_pdfs, extract_pdf
from ...utils.saver.write_file import create_saver
from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import (
    BasePipelineImpl,
    ExtractorProtocol,
    ProcessorProtocol,
    SaverProtocol,
)
from .bill_parser import parse_doc, parse_multiple_docs


class DocumentExtractor:
    """Extractor for document PDFs following ExtractorProtocol"""
    
    async def extract(self, new_bill_path: str, output_dir: str) -> Any:
        """Download assembly PDFs"""
        return await download_mass_assembly_pdfs(new_bill_path, output_dir=output_dir)


class PDFProcessor:
    """Processor for PDF documents following ProcessorProtocol"""
    
    async def process(self, data: str, **kwargs) -> None:
        """Extract text from PDFs"""
        await extract_multiple_pdfs(file_paths=data, method="pdfplumber")


class DocumentParser:
    """Parser for documents following ParserProtocol"""
    
    def __init__(self, saver: SaverProtocol):
        self.saver = saver
    
    async def parse(self, text_dir: str, **kwargs) -> Any:
        """Parse extracted text documents"""
        return await parse_multiple_docs(file_paths=text_dir, data_saver=self.saver)


class DocumentPipeline(BasePipelineImpl):
    """Pipeline for document processing and parsing"""
    
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
