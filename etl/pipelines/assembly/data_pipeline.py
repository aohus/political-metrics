import logging
from typing import Any, Dict

from ...utils.extract.api import APIExtractor
from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import (
    BasePipelineImpl,
    ExtractorProtocol,
    ProcessorProtocol,
    SaverProtocol,
)
from .api_metadata import AssemblyAPI
from .bill_processor import BillProcessor
from .proposer_processor import BillProposerProcessor


class AssemblyExtractor:
    """Extractor for assembly data following ExtractorProtocol"""

    def __init__(self, api_client: AssemblyAPI):
        self.api_client = api_client

    async def extract(self, request_apis: list[str], output_dir: str) -> dict[str, Any]:
        """Extract data from assembly APIs"""
        async with APIExtractor(self.api_client, output_dir) as extractor:
            multiple_requests = {api_name: dict() for api_name in request_apis}
            results = await extractor.extract_multiple(multiple_requests, is_save=True)
            return results


class AssemblyPipeline(BasePipelineImpl):
    """Pipeline for assembly data extraction and processing"""

    def __init__(self, config: Any):
        super().__init__(config, "AssemblyPipeline")
        self.extractor: ExtractorProtocol = AssemblyExtractor(AssemblyAPI())
        self.processors: list[ProcessorProtocol] = [
            BillProcessor(config),
            BillProposerProcessor(config)
        ]

    async def _execute_pipeline(self, request_apis: list[str]) -> dict[str, Any]:
        """Execute the assembly data pipeline"""
        data_paths = await self.stage_processor.execute_stage(
            "Data Extraction", 
            self.extractor.extract,
            request_apis,
            self.config.assembly_temp_raw
        )

        process_results = await self.stage_processor.execute_processors(
            self.processors,
            data_paths,
        )

        return {
            "data_paths": data_paths,
            "process_results": process_results,
            "status": "completed"
        }

    async def _cleanup(self):
        """Cleanup assembly pipeline resources"""
        self.logger.info("모든 어셈블리 세션이 정리되었습니다.")
        await super()._cleanup()