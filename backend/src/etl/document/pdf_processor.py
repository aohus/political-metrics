import asyncio
import logging
import os
import sys

# 현재 파일의 디렉토리를 sys.path에 추가하여 상대 경로 import가 가능하도록 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(parent_dir)

from etl.document.bill_parser import BillParser
from etl.utils.extract.download_file import download_mass_assembly_pdfs
from etl.utils.processor.pdf_reader import create_pdf_reader
from etl.utils.saver.write_file import create_saver

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
    "output_directory": "../../../data/documents/extracted_texts2",
    "add_timestamp": True,
    "create_subdirectories": True,
    "log_extractions": False,
}



class PDFProcessor:
    # TODO: parser, pdf_reader, saver 분리
    async def download(self, path: str) -> str:
        return await download_mass_assembly_pdfs(path)

    async def process(self, path: str) -> str:
        # pdf_dir = await self.download(path)
        config = {"reader_config": READER_CONFIG, "saver_config": SAVE_CONFIG}

        parser = BillParser(
            create_pdf_reader(),
            create_saver("../../../data/documents/extracted_texts2"),
            config=config,
        )
        return await parser.extract_multiple_files_batched(path)


async def main():
    path = "../../../data/documents/mass_bills_pdf/"
    processor = PDFProcessor()
    await processor.process(path)


if __name__ == "__main__":
    asyncio.run(main())
