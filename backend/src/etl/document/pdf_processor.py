import asyncio
import logging

from bill_pdf_parser.bill_parser import BillParser
from bill_pdf_parser.download_file import download_mass_assembly_pdfs
from bill_pdf_parser.pdf_reader import create_pdf_reader
from bill_pdf_parser.save_data import create_saver

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ 설정 파일 ============
READER_CONFIG = {
    "default_formats": [
        "structured",
        "json",
        "summary",
        "raw",
        "cleaned",
        "sections",
        "markdown",
    ],
    "method": [
        "pdfminer",
        # "pymupdf",
        # "pypdf2",
        # "best",
        # "pdfplumber",
    ],
}

SAVE_CONFIG = {
    "output_directory": "./bill_pdf_parser/extracted_texts",
    "add_timestamp": True,
    "create_subdirectories": True,
    "log_extractions": False,
}


class PDFProcessor:
    async def download(self, path: str) -> str:
        return await download_mass_assembly_pdfs(path)

    async def process(self, path: str) -> str:
        pdf_dir = await self.download(path)
        config = {"reader_config": READER_CONFIG, "saver_config": SAVE_CONFIG}

        parser = BillParser(
            create_pdf_reader(),
            create_saver(),
            config=config,
        )
        return await parser.extract_multiple_files_batched(pdf_dir)


async def main():
    path = "./bill_pdf_parser/mass_bills_pdf/"
    processor = PDFProcessor()
    await processor.process(path)


if __name__ == "__main__":
    asyncio.run(main())
