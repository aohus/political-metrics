import asyncio
import logging
import re

from .base_job import Processor

logger = logging.getLogger(__name__)


class GoalProcessor(Processor):
    def __init__(self, parser, writer, *args, **kwargs):
        self.job_map = {
            '외부환경': 'risk_manage',
            '기타': 'etc',
            '관리과제': 'task'
        }
        super().__init__(parser, writer, *args, **kwargs)

    async def get_job_type(self, part_title: str):
        if part_title in self.map.keys():
            return self.map.get(part_title)


class GoalParser:
    def __init__(self):
        self.compiler = re.compile(
            r'((?:\([1-9]\))\s*(?:외부환경.*?갈등관리계획|기타|관리과제별\s*추진계획))'
            r'(.*?)'
            r'(?=(?:\([1-9]\))\s*(?:기타|관리과제별\s*추진계획)|$)', 
            re.DOTALL | re.IGNORECASE
        )

    async def parse(self, content):
        lines = self.create_lines(content)
        for goal_title, line in lines:
            for match in self.compiler.finditer(line):
                yield goal_title, match[0], match[1]

    async def create_lines(self, content: str) -> iter[re.Match]:
        return self._create_lines(content)

    async def _create_lines(self, content: str) -> iter[re.Match]:
        pattern = r'(성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5])(.*?)(?=성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5]|전략목표\s*[ⅠⅡⅢⅣⅤ]|$)'
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).finditer(content)

