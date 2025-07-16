from typing import Any

from ...utils.extract.api import APIExtractor
from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import (
    BasePipelineImpl,
    ExtractorProtocol,
    ProcessorProtocol,
    SaverProtocol,
)
from .api_metadata import LawAPI


class LawExtractor:
    """Extractor for law data following ExtractorProtocol"""

    def __init__(self, api_client: LawAPI):
        self.api_client = api_client

    async def extract(self, request_apis: list[str], output_dir: str)-> dict[str, Any]:
        """Extract data from assembly APIs"""
        request_apis = request_apis or ["cur_law", "cur_admrul", "cur_ordin", "cur_trty"]
        async with APIExtractor(self.api_client, output_dir) as extractor:
            multiple_requests = {api_name: dict() for api_name in request_apis}
            results = await extractor.extract_multiple(multiple_requests, is_save=True)
            return results


class LawPipeline(BasePipelineImpl):
    """Pipeline for assembly data extraction and processing"""

    def __init__(self, config: Any):
        super().__init__(config, "AssemblyPipeline")
        self.extractor: ExtractorProtocol = LawExtractor(LawAPI())
        self.processors: list[ProcessorProtocol] = []

    async def _execute_pipeline(self, request_apis: list[str]) -> dict[str, Any]:
        """Execute the law data pipeline"""
        # Stage 1: Extract data
        data_paths = await self.stage_processor.execute_stage(
            "Data Extraction", 
            self.extractor.extract,
            request_apis,
            self.config.law_temp_raw
        )

        return {
            "data_paths": data_paths,
            "process_results": None,
            "status": "completed"
        }
