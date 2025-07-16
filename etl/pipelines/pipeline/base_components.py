import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from .protocols import ProcessorProtocol


class StageProcessor:
    """Utility class for processing pipeline stages with Protocol support"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def execute_stage(self, stage_name: str, stage_func, *args, **kwargs) -> Any:
        """Execute a single pipeline stage with logging"""
        self.logger.info(f"Starting stage: {stage_name}")
        start_time = datetime.now()
        
        try:
            result = await stage_func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Stage '{stage_name}' completed successfully in {duration:.2f}s")
            return result
        except Exception as e:
            self.logger.error(f"Stage '{stage_name}' failed: {e}")
            raise
    
    async def execute_parallel_stages(self, stages: list[tuple], return_exceptions: bool = True) -> list[Any]:
        """Execute multiple stages in parallel"""
        tasks = []
        for stage_name, stage_func, args, kwargs in stages:
            task = self.execute_stage(stage_name, stage_func, *args, **kwargs)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    
    async def execute_processors(self, processors: list[ProcessorProtocol], 
                               data: Any, config: Any, output_dir: str) -> list[Any]:
        """Execute multiple processors that follow ProcessorProtocol"""
        stages = [
            (f"Process {processor.__class__.__name__}", processor.process, (), {
                "data": data,
                "config": config,
                "output_dir": output_dir
            })
            for processor in processors
        ]
        
        return await self.execute_parallel_stages(stages)


class BasePipelineImpl:
    """Base implementation providing common pipeline functionality"""
    
    def __init__(self, config: Any, logger_name: str = None):
        self.config = config
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)
        self.stage_processor = StageProcessor(self.logger)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    async def run(self, **kwargs) -> dict[str, Any]:
        """Template method for pipeline execution"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.__class__.__name__} pipeline")
        
        try:
            result = await self._execute_pipeline(**kwargs)
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
            
            # Add metadata to result
            result.update({
                "pipeline_name": self.__class__.__name__,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration
            })
            
            return result
        except Exception as e:
            self.end_time = datetime.now()
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
        finally:
            await self._cleanup()
    
    async def _execute_pipeline(self, **kwargs) -> dict[str, Any]:
        """Override this method in concrete implementations"""
        raise NotImplementedError("Subclasses must implement _execute_pipeline")
    
    async def _cleanup(self):
        """Cleanup resources after pipeline execution"""
        self.logger.info("Pipeline cleanup completed")
