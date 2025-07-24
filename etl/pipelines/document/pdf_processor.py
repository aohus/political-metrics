from utils.pdf.pdf_reader import extract_multiple_pdfs


class PDFProcessor:
    async def process(self, data: str, **kwargs) -> None:
        await extract_multiple_pdfs(file_paths=data, method="pdfplumber")
