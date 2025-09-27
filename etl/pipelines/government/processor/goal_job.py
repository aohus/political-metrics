import logging
import re

import base_processor
from base_processor import ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class GoalProcessor(base_processor.BaseProcessor):
    def _get_job_type(self, title: str):
        job_map = {
            '(3)': 'risk',
            '(4)': 'etc',
            '(5)': 'task'
        }
        return job_map.get(title[0:3])


class GoalParser(base_processor.BaseParser):
    def __init__(self):
        self.compiler = re.compile(
            r'((?:\([1-9]\))\s*(?:외부환경.*?갈등관리계획|기타|관리과제별\s*추진계획))'
            r'(.*?)'
            r'(?=(?:\([1-9]\))\s*(?:기타|관리과제별\s*추진계획)|$)', 
            re.DOTALL | re.IGNORECASE
        )

    def parse(self, section):
        lines = self.create_lines(section)
        for matches in lines:
            goal_title, line = matches[0], matches[1]
            for match in self.compiler.finditer(line):
                yield ParsedInfo(event='request_job', 
                                 data={'key': {'title': goal_title}, 
                                       'section_title': match[1], 
                                       'section': match[2]})

    def create_lines(self, section: str) -> iter:
        return self._create_lines(section)

    def _create_lines(self, section: str) -> iter:
        pattern = r'(성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5])(.*?)(?=성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5]|전략목표\s*[ⅠⅡⅢⅣⅤ]|$)'
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(section)
