import asyncio
import logging

from base_processor import BaseParser, BaseProcessor
from config import JobConfig, JobConfigRegistry, JobType
from job import Job
from model import (
    Background,
    Effect,
    Etc,
    FinanceBusiness,
    Goal,
    Plan,
    Risk,
    SubTask,
    Target,
    Task,
)
from processor import (
    FinanceBusinessParser,
    FinanceBusinessProcessor,
    GoalParser,
    GoalProcessor,
    PlanParser,
    SubTaskNestedSectionParser,
    SubTaskSectionProcessor,
    TargetParser,
    TaskParser,
    TaskProcessor,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class Document:
    def __init__(self, _jobloop, name, job_configs, reader, writer):
        self._jobloop = _jobloop
        self.name = name
        self.job_configs = job_configs
        self.reader = reader
        self.writer = writer
        self.results = None
        self.ready_queue = asyncio.Queue()
        self._jobloop.docs.append(self)

    # async def run(self, fk, filepath):
    #     self.register(fk=fk, job_type='initial', filepath=filepath)

    def register(self, fk: str, job_type: JobType, filepath: str = None):
        if isinstance(job_type, str):
            d = {
                "goal": GovJobType.GOAL,
                "risk": GovJobType.RISK,
                "etc": GovJobType.ETC,
                "task": GovJobType.TASK,
                "finance": GovJobType.FINANCE,
                "subtasks": GovJobType.SUBTASKS,
                "target": GovJobType.TARGET,
                "effect": GovJobType.EFFECT,
                "background": GovJobType.BACKGROUND,
                "plan": GovJobType.PLAN,
            }
            job_type = d[job_type]

        if not filepath:
            filepath = self._make_filepath(fk, job_type.name)
        job = self._create_job(fk, job_type, filepath)
        self.ready_queue.put_nowait(job)
    
    def _create_processor(self, config):
        parser = config.parser_class()
        return config.processor_class(parser)

    def _create_job(self, fk, job_type, filepath):
        config = self.job_configs.get_config(job_type)
        processor = self._create_processor(config)
        return Job(doc=self, 
                   job_type=job_type, 
                   reader=self.reader, 
                   writer=self.writer, 
                   processor=processor,
                   fk=fk, 
                   dataclass_factory=config.data_class,
                   filepath=filepath)

    def _make_filepath(self, fk, job_type):
        return f"{self.name}_{fk}_{job_type}"


class GovJobType(JobType):
    GOAL = "성과목표"
    RISK = "갈등관리계획" 
    ETC = "기타"
    TASK = "관리과제"
    FINANCE = "관련재정사업"
    SUBTASKS = "세부사업내용"
    TARGET = "이해대상자"
    EFFECT = "기대효과"
    BACKGROUND = "추진배경"
    PLAN = "추진계획"


class GovGoalJobConfigRegistry(JobConfigRegistry):
    def __init__(self):
        self._configs: dict[GovJobType, JobConfig] = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        default_configs = {
            GovJobType.GOAL: JobConfig(
                processor_class=GoalProcessor, 
                parser_class=GoalParser,
                data_class=Goal
            ),
            GovJobType.RISK: JobConfig(
                processor_class=BaseProcessor, 
                parser_class=BaseParser,
                data_class=Risk
            ),
            GovJobType.ETC: JobConfig(
                processor_class=BaseProcessor, 
                parser_class=BaseParser,
                data_class=Etc
            ),
            GovJobType.TASK: JobConfig(
                processor_class=TaskProcessor,
                parser_class=TaskParser,
                data_class=Task
            ),
            GovJobType.FINANCE: JobConfig(
                processor_class=FinanceBusinessProcessor,
                parser_class=FinanceBusinessParser,
                data_class=FinanceBusiness
            ),
            GovJobType.SUBTASKS: JobConfig(
                processor_class=BaseProcessor,
                parser_class=SubTaskNestedSectionParser,
                data_class=SubTask
            ),
            GovJobType.TARGET: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=TargetParser,
                data_class=Target
            ),
            GovJobType.BACKGROUND: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=BaseParser,
                data_class=Background
            ),
            GovJobType.EFFECT: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=BaseParser,
                data_class=Effect
            ),
            GovJobType.PLAN: JobConfig( 
                processor_class=BaseProcessor,
                parser_class=PlanParser,
                data_class=Plan
            )
        }

        for job_type, config in default_configs.items():
            self.register(job_type, config)


# jobtype:
# remove_patterns = []
# section_pattern = ""
# line_pattern = ""
# info_pattern = ""
# get_job_type = ""

