from utils.download.base_downloader import FileDownloader, FileDownloadProgressor

from .doc_info_extractor import DocumentInfoExtractor


class DocumentExtractor:
    async def extract(self, new_bill_path: str, output_dir: str) -> any:
        info_extractor = DocumentInfoExtractor()
        file_downloader = FileDownloader()
        progressor = FileDownloadProgressor(info_extractor, file_downloader)
        return await progressor.download_all(new_bill_path, output_dir)
