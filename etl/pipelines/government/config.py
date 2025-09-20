from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from base_processor import BaseParser, BaseProcessor


class JobType(Enum):
    pass


@dataclass(frozen=True)  
class JobConfig:
    parser_class: BaseParser
    processor_class: BaseProcessor
    data_class: dataclass

    def __post_init__(self):
        if not all([self.parser_class, self.processor_class, self.data_class]):
            raise ValueError("All configuration classes must be provided")


class JobConfigRegistry:
    def __init__(self):
        self._configs: dict[JobType, JobConfig] = {}
        self._setup_default_configs()
        logger.info("Registered job configs")

    def _setup_default_configs(self):
        default_configs = {}

        for job_type, config in default_configs.items():
            self.register(job_type, config)

    def register(self, job_type: JobType, config: JobConfig):
        if not isinstance(job_type, JobType):
            raise TypeError(f"job_type must be JobType, got {type(job_type)}")
        self._configs[job_type] = config

    def get_config(self, job_type: JobType) -> Optional[JobConfig]:
        config = self._configs.get(job_type)
        if not config:
            raise ValueError(f"Unsupported job type: {job_type}")
        return config

    def get_supported_types(self) -> list[JobType]:
        return list(self._configs.keys())
