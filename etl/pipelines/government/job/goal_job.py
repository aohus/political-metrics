import asyncio
import logging
import re

from .base_job import BaseProcessor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class GoalProcessor(BaseProcessor):
    def __init__(self, parser, writer, *args, **kwargs):
        super().__init__(parser, writer, *args, **kwargs)
        self.job_map = {
            '(3)': 'risk_manage',
            '(4)': 'etc',
            '(5)': 'task'
        }
    
    async def create_data(self, data_class, title, fk):
        data = data_class(goal=title, goal_num=title, fk=fk)
        await self.writer.add(data.to_csv_row)
        return data.id
    
    async def get_job_type(self, part_title: str):
        if part_title[0:3] in self.job_map.keys():
            return self.job_map.get(part_title[0:3])


class GoalParser:
    def __init__(self):
        self.compiler = re.compile(
            r'((?:\([1-9]\))\s*(?:외부환경.*?갈등관리계획|기타|관리과제별\s*추진계획))'
            r'(.*?)'
            r'(?=(?:\([1-9]\))\s*(?:기타|관리과제별\s*추진계획)|$)', 
            re.DOTALL | re.IGNORECASE
        )

    async def parse(self, content):
        lines = await self.create_lines(content)
        for matches in lines:
            goal_title, line = matches[0], matches[1]
            for match in self.compiler.finditer(line):
                logging.info(f"goal-part: {goal_title} {match[1]}")
                yield (goal_title, match[1], match[2])

    async def create_lines(self, content: str) -> iter:
        return await self._create_lines(content)

    async def _create_lines(self, content: str) -> iter:
        pattern = r'(성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5])(.*?)(?=성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5]|전략목표\s*[ⅠⅡⅢⅣⅤ]|$)'
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(content)

