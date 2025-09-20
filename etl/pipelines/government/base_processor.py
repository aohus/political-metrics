import copy
import logging
import re
from dataclasses import dataclass
from typing import Optional

import job

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ParsedInfo:
    event: str  # "register_job", "create_data", "update_data"
    data: dict


class BaseProcessor(job.AbstractProcessor):
    def __init__(self, parser, *args, **kwargs):
        self.parser = parser
        self._memo = {}

    def process(self, content) -> iter:
        return self._process_lines(content)
    
    def _process_lines(self, content) -> iter:
        obj = {}
        for parsed in self.parser.parse(content):
            if parsed.event == 'update_data':
                completed_obj, obj = self._update_data(parsed.data, obj)
                if completed_obj:
                    yield ("create_data", completed_obj)
            elif parsed.event == 'create_data':
                yield (parsed.event, parsed.data)
            elif parsed.event == 'register_job':
                yield self._process_data(parsed)
            elif parsed.event == '':
                yield self._pick_event(parsed)
            else:
                logger.error(f'invalid event {parsed.event}')

    def _pick_event(self, parsed):
        """update data logic"""

    def _update_data(self, parsed_data: dict, obj: dict) -> tuple[Optional[dict], dict]:
        """update data logic"""
        pass

    def _process_data(self, parsed):
        title = parsed.data.get('section_title')
        parsed.data['job_type'] = self._get_job_type(title)
        return (parsed.event, parsed.data)
    
    def _get_job_type(self, content):
        """update data logic"""
        raise NotImplementedError


class BaseParser(job.AbstractParser):
    def __init__(self):
        self.compiler = re.compile(r'([ㅇ◦□]\s*.+?)(?=ㅇ|◦|□|$)', re.DOTALL | re.IGNORECASE)

    def create_lines(self, content: str):
        if content:
            return self._create_lines(content)

    def _create_lines(self, content: str):
        return [content]

    def parse(self, content: str):
        lines = self._create_lines(content)
        return self._parse(lines)

    def _parse(self, lines: list) -> iter:
        for line in lines:
            for matches in self.compiler.finditer(line):
                content = matches[1].replace('\n', '\\n')
                if not content:
                    logger.error('content not found')
                    continue
                yield ParsedInfo(event='create_data', data={'content': content})


class BaseNestedParser(BaseParser):
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


