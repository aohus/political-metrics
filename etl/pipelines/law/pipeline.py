from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import ExtractorProtocol, ProcessorProtocol
from .law_extractor import LawExtractor


class LawPipeline(BasePipelineImpl):
    """Pipeline for assembly data extraction and processing"""

    def __init__(self, config: any):
        super().__init__(config, "AssemblyPipeline")
        self.extractor: ExtractorProtocol = LawExtractor()
        self.processors: list[ProcessorProtocol] = []

    async def _execute_pipeline(self, request_apis: list[str]) -> dict[str, any]:
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
