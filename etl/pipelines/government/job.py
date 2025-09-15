
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Protocol, Tuple, Type

logger = logging.getLogger(__name__)


class ProcessorProtocol(Protocol):
    def process(self, data: Any) -> Any: ...


class ParserProtocol(Protocol):
    def create_lines(self, content: str) -> Any: ...
    def parse_lines(self, lines: list) -> Any: ...


class DataClassProtocol(Protocol):
    pass


class Linker:
    goal: str
    task: str = None


class Job:
    mamanger: Manager
    linker: Linker
    processor: Processor
    content: str

    def process(self):
        self.processor.parse(self.content)


class JobType(Enum):
    GOAL = "goal"
    RISK = "risk" 
    ETC = "etc"  # 'etc' 대신 명확한 이름 사용
    TASK = "task"
    FINANCE = "finance"
    SUBTASKS = "subtasks"
    GENERAL = "general"


@dataclass(frozen=True)  
class JobConfig:
    """Job 생성을 위한 설정 정보"""
    parser_class: Type[ParserProtocol]
    processor_class: Type[ProcessorProtocol]
    data_class: Type[DataClassProtocol]
    
    def __post_init__(self):
        """설정 유효성 검증"""
        if not all([self.parser_class, self.processor_class, self.data_class]):
            raise ValueError("All configuration classes must be provided")


class JobConfigRegistry:
    """Job 설정을 관리하는 레지스트리"""
    
    def __init__(self):
        self._configs: Dict[JobType, JobConfig] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """기본 설정들을 등록"""
        default_configs = {
            JobType.GOAL: JobConfig(
                parser_class=GoalParser,
                processor_class=GoalProcessor, 
                data_class=Goal
            ),
            JobType.RISK: JobConfig(
                parser_class=RiskManageParser,
                processor_class=RiskManageProcessor,  # 수정: 괄호 제거
                data_class=RiskManage
            ),
            JobType.TASK: JobConfig(
                parser_class=TaskParser,
                processor_class=TaskProcessor,
                data_class=Task
            ),
            JobType.FINANCE: JobConfig(
                parser_class=FinanceSectionParser,
                processor_class=FinanceSectionProcessor,
                data_class=FinanceSection
            ),
            JobType.SUBTASKS: JobConfig(
                parser_class=SubTaskNestedSectionParser,
                processor_class=SubTaskSectionProcessor,
                data_class=SubTaskSection
            ),
            JobType.SECTION: JobConfig(  # 'etc' 중복 해결
                parser_class=SectionParser,
                processor_class=SectionProcessor,
                data_class=SectionData
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


class AbstractJobFactory(ABC):
    @abstractmethod
    def create_job(self, manager: Any, job_type: JobType, 
                   content: str, linker: Any) -> 'Job':
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list[JobType]:
        """지원되는 타입 목록"""
        pass


class JobFactory(AbstractJobFactory):
    def __init__(self, config_registry: Optional[JobConfigRegistry] = None):
        self._config_registry = config_registry or JobConfigRegistry()
        self._parser_cache: Dict[JobType, ParserProtocol] = {}
        self._processor_cache: Dict[JobType, ProcessorProtocol] = {}
    
    def _get_or_create_processor(self, job_type: JobType) -> ProcessorProtocol:
        if job_type not in self._processor_cache:
            config = self._config_registry.get_config(job_type)
            if not config:
                raise ValueError(f"Unsupported job type: {job_type.value}")
            
            try:
                processor = config.processor_class(config.data_class)
                self._processor_cache[job_type] = processor
                logger.debug(f"Created processor for {job_type.value}")
            except Exception as e:
                logger.error(f"Failed to create processor for {job_type.value}: {e}")
                raise
        
        return self._processor_cache[job_type]
    
    def _get_or_create_parser(self, job_type: JobType) -> ParserProtocol:
        if job_type not in self._parser_cache:
            config = self._config_registry.get_config(job_type)
            if not config:
                raise ValueError(f"Unsupported job type: {job_type.value}")
            
            try:
                processor = self._get_or_create_processor(job_type)
                parser = config.parser_class(processor)
                self._parser_cache[job_type] = parser
                logger.debug(f"Created parser for {job_type.value}")
            except Exception as e:
                logger.error(f"Failed to create parser for {job_type.value}: {e}")
                raise
        
        return self._parser_cache[job_type]
    
    def create_job(self, manager: Any, job_type: JobType, 
                   content: str, linker: Any) -> 'Job':
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
            # JobType이 문자열로 전달된 경우 변환
            if isinstance(job_type, str):
                job_type = JobType(job_type)
            
            parser = self._get_or_create_parser(job_type)
            
            job = Job(
                manager=manager,
                parser=parser, 
                content=content,
                linker=linker
            )
            
            logger.info(f"Successfully created job of type: {job_type.value}")
            return job
            
        except ValueError as e:
            logger.error(f"Invalid job type: {job_type}")
            raise
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise RuntimeError(f"Job creation failed: {e}") from e
    
    def get_supported_types(self) -> list[JobType]:
        return self._config_registry.get_supported_types()
    
    def register_job_type(self, job_type: JobType, config: JobConfig):
        self._config_registry.register(job_type, config)
        self._parser_cache.pop(job_type, None)
        self._processor_cache.pop(job_type, None)
    
    def clear_cache(self):
        self._parser_cache.clear()
        self._processor_cache.clear()
        logger.info("Factory cache cleared")


class SingletonJobFactory(JobFactory):
    _instance: Optional['SingletonJobFactory'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_registry: Optional[JobConfigRegistry] = None):
        if not self._initialized:
            super().__init__(config_registry)
            self._initialized = True