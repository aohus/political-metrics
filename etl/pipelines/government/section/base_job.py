import copy
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Protocol, Tuple, Type

# 로깅 설정
logger = logging.getLogger(__name__)


@dataclass
class Result:
    status: int
    data: dict
    total: int
    success: int
    error_msg: str


class BaseProcessor:
    def __init__(self, parser, data_cls):
        self.parser = parser
        self.data_cls = data_cls

    def process(self, content):
        self.create_lines(content)
    
    def create_lines(self, content):
        lines = self.parser.create_lines(content)
        self.process_lines(lines)
    
    def process_lines(self, lines):
        obj = self.create_obj()

        for data in self.parser.parse_lines(lines):
            self.insert(obj, *data)
    
    def insert(self, obj=None, *data):
        pass

    def create_obj(self, obj=None):
        return self.obj_cls()

    def to_dict(self):
        return {}


class BaseParser:
    def __init__(self):
        self.compiler = re.compile()

    def create_lines(self, section: str):
        return self._create_lines(section)

    def _create_lines(self, section: str):
        return section.split("\n")

    def parse_lines(self, lines):
        for line in lines:
            self._parse_lines(line)

    def _parse_lines(self, line: str) -> iter:
        return self.compiler.finditer(line)


class BaseNestedParser:
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
    
    def process_line(self):
        line = self._get_line()
        if not line:
            return "eof", {}
        return self._process_line(line)

    def _process_line(self, line):
        pass
    
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


