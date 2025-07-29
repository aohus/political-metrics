from ..pipeline.base_components import BasePipelineImpl
from ..pipeline.protocols import ExtractorProtocol, ProcessorProtocol, SaverProtocol

# Import necessary components
from .assembly_extractor import AssemblyExtractor
from .bill_processor import BillProcessor
from .new_bill_processor import write_new_bills
from .proposer_processor import BillProposerProcessor


class AssemblyPipeline(BasePipelineImpl):
    """Pipeline for assembly data extraction and processing"""

    def __init__(self, config: any):
        super().__init__(config, "AssemblyPipeline")
        self.extractor: ExtractorProtocol = AssemblyExtractor()
        self.processors: list[ProcessorProtocol] = [
            BillProcessor(config),
            BillProposerProcessor(config)
        ]
        self.write_new_bills = write_new_bills

    async def _execute_pipeline(self, request_apis: list[str]) -> dict[str, any]:
        """Execute the assembly data pipeline"""
        extract_results = await self.stage_processor.execute_stage(
            "Data Extraction", 
            self.extractor.extract,
            request_apis,
            self.config.assembly_temp_raw
        )

        processed_results = await self.stage_processor.execute_processors(
            self.processors,
            extract_results,
        )

        new_bill_results = await self.stage_processor.execute_stage(
            "Write New Bills", 
            self.write_new_bills,
        )
        return {
            "extract_results": extract_results,
            "process_results": processed_results,
            "new_bill_chunks": new_bill_results,
            "status": "completed"
        }

    async def _cleanup(self):
        """Cleanup assembly pipeline resources"""
        self.logger.info("모든 어셈블리 세션이 정리되었습니다.")
        await super()._cleanup()