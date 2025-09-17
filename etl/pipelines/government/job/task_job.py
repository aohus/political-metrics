import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .base_job import BaseProcessor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class EtcParser:
    def parse(self, content: str):
        return content


class RiskManagePlanParser:
    def parse(self, content: str):
        return content


class TaskProcessor(BaseProcessor):
    def __init__(self, parser, writer, *args, **kwargs):
        super().__init__(parser, writer, *args, **kwargs)
        self.job_map = {
            '추진': 'background',
            '주요': 'subtasks',
            '수혜': 'general',
            '기대': 'general',
            '관련': 'finance',
            '년도': 'general',
            '22': 'general',
            '23': 'general',
            '24': 'general',
        }

    async def get_job_type(self, section_title: str):
        return self.job_map.get(section_title[0:2])


class TaskParser:
    def __init__(self):
        self.compiler = re.compile(
                r'□?\s*(?P<section_title>추진\s*배경\s*.*?|주요\s*내용.*?|수혜자\s*및.*?|기대\s*효과.*?|관련\s*재정.*?|[1-9]{0,2}\s*년도\s*과제\s*추진\s*계획.*?)'
                r'\n(?P<section_content>.*?)'
                r'(?=추진\s*배경|(?:□\s*)주요\s*내용\s*및|[^\(]수혜자\s*및|성과지표\s*및|수혜자\s*체감도|기대\s*효과|관련\s*재정|[1-3]{0,2}\s*년도\s*과제\s*추진\s*계획|$)'
                , re.DOTALL | re.IGNORECASE)

    async def create_lines(self, content: str):
        return await self._create_lines(content)
    
    async def _create_lines(self, content: str):
        """
        성과목표(goal)에서 '관리과제'(task) 리스트 추출
        성과목표Ⅰ-1 [① 관리과제, ... , ⑥ 관리과제]
        """
        pattern = (
            r'[\uf000-\U000fffff]\s*(?P<task_title>.{1,50})'
            r'(\([ⅠⅡⅢⅣⅤ1234567①②③④⑤⑥⑦⑧⑨⑩\-]+?\))'
            r'\n(?P<task_content>□?\s*추진\s*배경.+?)'
            r'(?=[\uf000-\U000fffff]\s*.{1,50}□?\s*추진\s*배경|Ⅳ\s|$)'
        )
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).finditer(content)

    async def parse(self, title: str, content: str):
        """
        '관리과제(task)의 주요 정보(section)' 추출
        Ⅰ-1-① : [배경, 대상, 주요내용(사업 리스트), 계획, 재정사업, 기대효과]
        """
        lines = await self.create_lines(content)
        for line in lines:
            for match in self.compilers.get('task').finditer(line):
                yield title, match.group("section_title"), match.group("section_content")
