# from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, Optional, Type

from job import (
    BaseParser,
    BaseProcessor,
    DataClassProtocol,
    FinanceBusinessParser,
    FinanceBusinessProcessor,
    GoalParser,
    GoalProcessor,
    ParserProtocol,
    ProcessorProtocol,
    SubTaskNestedSectionParser,
    SubTaskSectionProcessor,
    TaskParser,
    TaskProcessor,
)
from manager import Manager
from model import (
    Background,
    Effect,
    Etc,
    FinanceBusiness,
    Goal,
    RiskManagePlan,
    SubTask,
    Target,
    Task,
)
from writer import Writer

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class Job:
    def __init__(self, manager, processor, data_class, content, fk):
        self.manager: Manager = manager
        self.processor: ProcessorProtocol = processor
        self.data_class: dataclass = data_class
        self.content: str = content
        self.fk: str = fk

    async def process(self):
        await self.processor.process(self)


class JobType(Enum):
    GOAL = "goal"
    RISK = "risk" 
    ETC = "etc"
    TASK = "task"
    FINANCE = "finance"
    SUBTASKS = "subtasks"
    TARGET = "target"
    EFFECT = "effect"
    BACKGROUND = "background"
    PLAN = "plan"


@dataclass(frozen=True)  
class JobConfig:
    parser_class: Type[ParserProtocol]
    processor_class: Type[ProcessorProtocol]
    data_class: Type[DataClassProtocol]

    def __post_init__(self):
        if not all([self.parser_class, self.processor_class, self.data_class]):
            raise ValueError("All configuration classes must be provided")


class JobConfigRegistry:
    def __init__(self):
        self._configs: dict[JobType, JobConfig] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        default_configs = {
            JobType.GOAL: JobConfig(
                processor_class=GoalProcessor, 
                parser_class=GoalParser,
                data_class=Goal
            ),
            JobType.RISK: JobConfig(
                processor_class=BaseProcessor, 
                parser_class=BaseParser,
                data_class=RiskManagePlan
            ),
            JobType.ETC: JobConfig(
                processor_class=BaseProcessor, 
                parser_class=BaseParser,
                data_class=Etc
            ),
            JobType.TASK: JobConfig(
                processor_class=TaskProcessor,
                parser_class=TaskParser,
                data_class=Task
            ),
            JobType.FINANCE: JobConfig(
                processor_class=FinanceBusinessProcessor,
                parser_class=FinanceBusinessParser,
                data_class=FinanceBusiness
            ),
            JobType.SUBTASKS: JobConfig(
                processor_class=SubTaskSectionProcessor,
                parser_class=SubTaskNestedSectionParser,
                data_class=SubTask
            ),
            JobType.TARGET: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=BaseParser,
                data_class=Target
            ),
            JobType.BACKGROUND: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=BaseParser,
                data_class=Background
            ),
            JobType.EFFECT: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=BaseParser,
                data_class=Effect
            )
        }
        
        for job_type, config in default_configs.items():
            self.register(job_type, config)
    
    def register(self, job_type: JobType, config: JobConfig):
        if not isinstance(job_type, JobType):
            raise TypeError(f"job_type must be JobType, got {type(job_type)}")
        
        self._configs[job_type] = config
        logger.info(f"Registered job type: {job_type.value}")
    
    def get_config(self, job_type: JobType) -> Optional[JobConfig]:
        return self._configs.get(job_type)
    
    def get_supported_types(self) -> list[JobType]:
        return list(self._configs.keys())


class CacheObj:
    def __init__(self):
        self._parser_cache: dict[JobType, ParserProtocol] = {}
        self._processor_cache: dict[JobType, ProcessorProtocol] = {}
        self._writer_cache: dict[JobType, Writer] = {}


class JobFactory:
    def __init__(self, cache_obj: CacheObj, create_writer, config_registry: Optional[JobConfigRegistry] = None):
        self._config_registry = config_registry or JobConfigRegistry()
        self._parser_cache = cache_obj._parser_cache
        self._processor_cache = cache_obj._processor_cache
        self._writer_cache = cache_obj._writer_cache
        self.create_writer = create_writer
    
    def _get_config(self, job_type: JobType) -> bool:
        config = self._config_registry.get_config(job_type)
        if not config:
            raise ValueError(f"Unsupported job type: {job_type.value}")
        return config
            
    def _get_or_create_parser(self, config, job_type: JobType) -> ParserProtocol:
        if job_type not in self._parser_cache:
            try:
                parser = config.parser_class()
                self._parser_cache[job_type] = parser
                logger.debug(f"Created parser for {job_type.value}")
            except Exception as e:
                logger.error(f"Failed to create parser for {job_type.value}: {e}")
                raise
        return self._parser_cache[job_type]
    
    def _get_or_create_processor(self, config, job_type: JobType) -> ProcessorProtocol:
        if job_type not in self._processor_cache:
            try:
                parser = self._get_or_create_parser(config, job_type)
                writer = self.create_writer(job_type, config.data_class.header, 10)
                processor = config.processor_class(parser, writer)
                self._processor_cache[job_type] = processor
                logger.debug(f"Created processor for {job_type.value}")
            except Exception as e:
                logger.error(f"Failed to create processor for {job_type.value}: {e}")
                raise
        return self._processor_cache[job_type]
    
    def _get_data_class(self, config) -> ProcessorProtocol:
        return config.data_class
    
    async def create_job(self, manager: Any, job_type: JobType, content: str, fk: Any) -> 'Job':
        """
        Job을 생성하고 반환
        
        Args:
            manager: Job 매니저
            job_type: 생성할 Job의 타입
            content: 처리할 콘텐츠
            linker: 링커 객체
            
        Returns:
            생성된 Job 인스턴스
            
        Raises:
            ValueError: 지원되지 않는 Job 타입
            RuntimeError: Job 생성 실패
        """
        try:
            if isinstance(job_type, str):
                job_type = JobType(job_type)
            config = self._get_config(job_type)            
            processor = self._get_or_create_processor(config, job_type)
            data_class = self._get_data_class(config)
            
            job = Job(
                manager=manager,
                content=content,
                processor=processor,
                data_class=data_class,
                fk=fk
            )
            logger.info(f"Successfully created job of type: {job_type.value}")
            return job
            
        except ValueError as e:
            logger.error(f"Invalid job type: {job_type}")
            raise
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise RuntimeError(f"Job creation failed: {e}") from e
    
    async def get_supported_types(self) -> list[JobType]:
        return self._config_registry.get_supported_types()
    
    async def register_job_type(self, job_type: JobType, config: JobConfig):
        self._config_registry.register(job_type, config)
        self._parser_cache.pop(job_type, None)
        self._processor_cache.pop(job_type, None)
    
    async def clear_cache(self):
        self._parser_cache.clear()
        self._processor_cache.clear()
        logger.info("Factory cache cleared")


class SingletonJobFactory(JobFactory):
    _instance: Optional['SingletonJobFactory'] = None
    _initialized: bool = False

    async def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def __init__(self, config_registry: Optional[JobConfigRegistry] = None):
        if not self._initialized:
            super().__init__(config_registry)
            self._initialized = True