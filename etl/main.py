import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from pipelines.assembly.data_pipeline import AssemblyPipeline
from pipelines.document.data_pipeline import DocumentPipeline
from pipelines.pipeline.protocols import PipelineProtocol

from .configs import PathConfig
from .utils.file.fileio import read_file, write_file


class PipelineOrchestrator:
    """Orchestrates multiple pipelines using Protocol-based design"""
    
    def __init__(self, config_path: str):
        self.config = PathConfig(config_path)
        self.logger = logging.getLogger("PipelineOrchestrator")
        self._pipelines: dict[str, PipelineProtocol] = {}
        self._initialize_pipelines()
    
    def _initialize_pipelines(self):
        """Initialize all available pipelines"""
        self._pipelines = {
            "assembly": AssemblyPipeline(self.config),
            "document": DocumentPipeline(self.config)
        }
    
    async def run_pipeline(self, pipeline_name: str, **kwargs) -> dict[str, Any]:
        """Run a specific pipeline by name"""
        if pipeline_name not in self._pipelines:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")
        
        pipeline = self._pipelines[pipeline_name]
        self.logger.info(f"Starting pipeline: {pipeline_name}")
        
        return await pipeline.run(**kwargs)
    
    async def run_all_pipelines(self) -> dict[str, Any]:
        """Run all pipelines in sequence"""
        results = {}
        
        try:
            # Run assembly pipeline
            assembly_result = await self.run_pipeline(
                "assembly",
                request_apis=["law_bill_member", "law_bill_gov", "law_bill_cap", "taking"]
            )
            results["assembly"] = assembly_result
            
            # Process new bills
            new_bills = await self._process_new_bills()
            results["new_bills_count"] = len(new_bills) if new_bills else 0
            
            # Run document pipeline
            document_result = await self.run_pipeline("document")
            results["document"] = document_result
            
            results["status"] = "all_completed"
            self.logger.info("All pipelines completed successfully")
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            self.logger.error(f"Pipeline orchestration failed: {e}", exc_info=True)
            raise
        
        return results
    
    async def _process_new_bills(self) -> Optional[list[tuple]]:
        """Identify and save new bills"""
        try:
            new_bills_path = self.config.assembly_temp_formatted / "bills.json"
            old_bills_path = self.config.assembly_formatted / "bills.json"
            
            # Read both files
            new_bills, old_bills = await asyncio.gather(
                read_file(new_bills_path),
                read_file(old_bills_path)
            )
            
            # Find new bills
            old_bill_no = {bill["BILL_NO"] for bill in old_bills}
            new_bills_list = [
                (bill["BILL_ID"], f"{bill['BILL_NO']}_{bill['BILL_NAME']}")
                for bill in new_bills
                if bill["BILL_NO"] not in old_bill_no
            ]
            
            # Save new bills
            if new_bills_list:
                date_str = datetime.now().strftime("%Y-%m-%d")
                output_path = self.config.assembly_ref / f"new_bill_{date_str}.json"
                await write_file(output_path, new_bills_list)
                self.logger.info(f"Found {len(new_bills_list)} new bills")
            
            return new_bills_list
            
        except Exception as e:
            self.logger.error(f"Failed to process new bills: {e}")
            return None
    
    def add_pipeline(self, name: str, pipeline: PipelineProtocol):
        """Add a new pipeline dynamically"""
        self._pipelines[name] = pipeline
        self.logger.info(f"Added pipeline: {name}")
    
    def get_available_pipelines(self) -> list[str]:
        """Get list of available pipeline names"""
        return list(self._pipelines.keys())


async def main():
    """Main entry point for the ETL pipeline"""
    config_path = "etl/configs/config.yaml"
    orchestrator = PipelineOrchestrator(config_path)
    
    try:
        # Show available pipelines
        available = orchestrator.get_available_pipelines()
        print(f"Available pipelines: {', '.join(available)}")
        
        # Run all pipelines
        results = await orchestrator.run_all_pipelines()
        print(f"Pipeline execution completed: {results['status']}")
        
        if results.get('new_bills_count'):
            print(f"Found {results['new_bills_count']} new bills")
            
        # Print timing information
        for pipeline_name, result in results.items():
            if isinstance(result, dict) and 'duration_seconds' in result:
                print(f"{pipeline_name}: {result['duration_seconds']:.2f}s")
                
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())