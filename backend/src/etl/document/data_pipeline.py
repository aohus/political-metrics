import logging

from .bill_parser import BillParser
from ..utils.extract.download_file import download_mass_assembly_pdfs
from ..utils.processor.pdf_reader import create_pdf_reader
from ..utils.saver.write_file import create_saver

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


parser_config = {"reader_config": READER_CONFIG, "saver_config": SAVE_CONFIG}


async def run(config):
    document_pdf_path = config.document_pdf
    document_formatted_path = config.document_formatted

    await download_mass_assembly_pdfs(document_pdf_path)

    parser = BillParser(
        create_pdf_reader(),
        create_saver(document_formatted_path),
        config=parser_config,
    )
    return await parser.extract_multiple_files_batched(document_pdf_path)


