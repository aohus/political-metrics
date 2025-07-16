from ...utils.api.api_extractor import APIExtractor
from .api_metadata import AssemblyAPI


class AssemblyExtractor:
    """Extractor for assembly data following ExtractorProtocol"""

    def __init__(self, api_client: AssemblyAPI):
        self.api_client = api_client

    async def extract(self, request_apis: list[str], output_dir: str) -> dict[str, any]:
        """Extract data from assembly APIs"""
        async with APIExtractor(self.api_client, output_dir) as extractor:
            multiple_requests = {api_name: dict() for api_name in request_apis}
            results = await extractor.extract_multiple(multiple_requests, is_save=True)
            return results
