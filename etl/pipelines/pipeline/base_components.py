import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

from .protocols import ProcessorProtocol


@dataclass
class ProcessorConfig:
    name: str
    processor: str
    run_func: str = 'process'
    init_args: dict[str, Any] = {}
    kwargs: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StageProcessor:
    """Utility class for processing pipeline stages with Protocol support"""    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.stages = []

    def add_stage(self, name: str, processor_cls: str, run_func: str, init_args: dict[str, Any], kwargs: dict[str, Any]) -> None:
        self.logger.info(f"Adding processor: {name} ({processor_cls.__name__})")
        if not processor_cls or not issubclass(processor_cls, ProcessorProtocol):
            raise ValueError(f"Processor class {processor_cls.__name__} not found or does not implement ProcessorProtocol")
        
        processor = processor_cls(**init_args)
        run_method = getattr(processor, run_func)
        self.stages.append(
            (name, run_method, (), kwargs)
        )

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
    
    async def execute_stages(self, return_exceptions: bool = True) -> list[Any]:
        if not self.stages:
            self.logger.warning("No stages to execute")
            return []
        
        if len(self.stages) == 1:
            stage_name, stage_func, args, kwargs = self.stages[0]
            return [await self.execute_stage(stage_name, stage_func, *args, **kwargs)]
        
        tasks = []
        for stage_name, stage_func, args, kwargs in self.stages:
            task = self.execute_stage(stage_name, stage_func, *args, **kwargs)
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)


class BasePipelineImpl:
    """Base implementation providing common pipeline functionality"""
    
    def __init__(self, config: Any, logger_name: str = None):
        self.config = config
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)
        self.processor_factory: list[tuple[str, list[ProcessorConfig]]] = []
        self.stage_processor = StageProcessor(self.logger)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    async def run(self, **kwargs) -> dict[str, Any]:
        """Template method for pipeline execution"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.__class__.__name__} pipeline")
        
        try:
            result = await self.execute_pipeline(**kwargs)
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
    
    async def execute_pipeline(self, **kwargs) -> dict[str, Any]:
        for step, processors in self.processor_factory:
            for processor in processors:
                self.stage_processor.add_stage(
                    processor.name if hasattr(processor, 'name') else processor.__name__,
                    processor.processor,
                    processor.run_func,
                    processor.init_args,
                    processor.kwargs
                )
            await self.stage_processor.execute_stages()
    
    async def _cleanup(self):
        """Cleanup resources after pipeline execution"""
        self.logger.info("Pipeline cleanup completed")
