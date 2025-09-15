import asyncio
import copy
import logging
import re
from typing import Any, Dict, Optional, Protocol, Tuple, Type

logger = logging.getLogger(__name__)


class ProcessorProtocol(Protocol):
    async def process(self, data: Any) -> Any: ...
    
    async def process_lines(self, data: Any) -> Any: ...
    
    async def update_data(self, data: Any) -> Any: ...
    
    async def create_data(self, data: Any) -> Any: ...


class ParserProtocol(Protocol):
    async def parse(self, lines: list) -> Any: ...


class DataClassProtocol(Protocol):
    def to_dict(self) -> dict: ...


class BaseProcessor:
    def __init__(self, parser, writer, *args, **kwargs):
        self.parser = parser
        self.writer = writer
        self.job_map = {}

    async def process(self, job):
        await self.process_lines(job)
    
    async def process_lines(self, job):
        for title, section_title, section_content in self.parser.parse_lines(job.content):
            fk = await self.create_data(job.data_class, title)
            await self.request_job(job.manager, fk, section_title, section_content)

    async def create_data(self, data_class, task_title):
        data = data_class(title=task_title)
        return data.id

    async def update_data(self, data, infos):
        data.f = infos
    
    async def request_job(self, manager: Manager, fk, section_title, section_content):
        if not (section_title or section_content):
            logger.warning("section_title, section_content is Required")
        
        if job_type := self.get_job_type(section_title):
            asyncio.create_task(manager.add(job_type, section_content, fk))

    async def get_job_type(self, section_title: str):
        return self.job_map.get(section_title)


class BaseParser:
    def __init__(self):
        self.compiler = re.compile(r'([ㅇ◦]\s*.+?)(?=ㅇ|◦|$)', re.DOTALL | re.IGNORECASE)

    async def create_lines(self, section: str):
        return await self._create_lines(section)

    async def _create_lines(self, section: str):
        return section.split("\n")
    
    async def parse_lines(self, lines: list):
        for line in lines:
            return await self._parse_lines(line)

    async def _parse_lines(self, line: str) -> iter:
        return self.compiler.finditer(line)
    
    async def parse(self, content) -> iter:
        for matches in self.compiler.finditer(content):
            yield matches

    async def parse_with_line(self, content) -> iter:
        lines = self.create_lines(content)
        for line in lines:
            for matches in self.compiler.finditer(line):
                yield matches


class NestedParser:
    def __init__(self):
        self.infos = []
        self.lines = []
        self.map = set()
        self.step = 0
        self.max_step = 0
        self.section_title = ""
    
    def _get_initial_sep(self):
        try:
            return self.lines[0][0]
        except:
            print("no sections", self.lines)
    
    def _get_line(self):
        while True:
            if self.step >= self.max_step:
                return 
            
            line = self.lines[self.step]
            if self._line_validation(line):
                return line
            self.step += 1
            
    def _line_validation(self, line):
        return len(line) > 0
    
    def parse_lines(self):
        line = self._get_line()
        if not line:
            return "eof", {}
        return self._process_line(line)

    def _parse_lines(self, line):
        pass
    
    def create_lines(self, content: str):
        return self._create_lines(content)
    
    def _create_lines(self, section: str):
        self.lines = [line for line in section.split('\n') if line]
        self.max_step = len(self.lines)
    
    def process(self, section):
        self._create_lines(section)
        self.nested_processor()
        return self.infos
    
    def nested_processor(self, last_stage_no: str = None, sep: str = None, map: set = set(), **info):
        n = 0
        if not sep:
            sep = self._get_initial_sep()
            map = {sep}

        stage_map = copy.deepcopy(map)
        stage_sep = cur_sep = sep
        stage_map.add(cur_sep)
        try:
            while True:
                cur_sep, info = self.process_line()
                if cur_sep == 'eof':
                    return 'eof', {}
                
                if cur_sep != stage_sep:
                    if cur_sep not in stage_map:
                        cur_sep, info = self.nested_processor(last_stage_no=stage_no, sep=cur_sep, map=stage_map, info=info)
                        if cur_sep != stage_sep:
                            return cur_sep, info
                    else:
                        return cur_sep, info
                
                n += 1
                stage_no = f'{last_stage_no}-{n}' if last_stage_no else str(n)
                
                info['no'] = stage_no
                self.infos.append(info)
                self.step += 1
        except Exception as e:
            print('info: ', info)


