from utils.download.base_downloader import FileDownloader

from .document_info_extractor import DocumentInfoExtractor


class DocumentExtractor:
    async def extract(self, new_bill_path: str, output_dir: str) -> any:
        info_extractor = DocumentInfoExtractor()
        async with FileDownloader(info_extractor=info_extractor) as downloader:
            results = await downloader.download_all(new_bill_path, output_dir)
            return results
