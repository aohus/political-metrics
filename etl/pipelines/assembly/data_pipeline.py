import logging

from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import ExtractorProtocol, ProcessorProtocol, SaverProtocol
from .api_metadata import AssemblyAPI
from .assembly_extractor import AssemblyExtractor
from .bill_processor import BillProcessor
from .proposer_processor import BillProposerProcessor


class AssemblyPipeline(BasePipelineImpl):
    """Pipeline for assembly data extraction and processing"""

    def __init__(self, config: any):
        super().__init__(config, "AssemblyPipeline")
        self.extractor: ExtractorProtocol = AssemblyExtractor(AssemblyAPI())
        self.processors: list[ProcessorProtocol] = [
            BillProcessor(config),
            BillProposerProcessor(config)
        ]

    async def _execute_pipeline(self, request_apis: list[str]) -> dict[str, any]:
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