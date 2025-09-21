import logging
import re

import base_processor
from base_processor import ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class GoalProcessor(base_processor.BaseProcessor):
    def _process_data(self, parsed):
        title = parsed.data.get('section_title')
        parsed.data['job_type'] = self._get_job_type(title)
        return (parsed.event, parsed.data)
    
    def _get_job_type(self, title: str):
        job_map = {
            '외부환경': 'risk',
            '기타': 'etc',
            '관리과제': 'task'
        }
        return job_map.get(title)


class GoalParser(base_processor.BaseParser):
    def __init__(self):
        self.compiler = re.compile(
            r'((?:\([3-5]\))\s*(외부환경|기타|관리과제).*?\n)'
            r'(.*?)'
            r'(?=(?:\([3-5]\))\s*(?:기타|관리과제별\s*추진계획)|$)', 
            re.DOTALL | re.IGNORECASE
        )

    def parse(self, content):
        lines = self.create_lines(content)
        for matches in lines:
            goal_title, line = matches[0], matches[1]
            for match in self.compiler.finditer(line):
                _, section_title, section = match.groups()
                if not (section_title or section):
                    logger.error(f"goal_title: {goal_title} has no section({section[0:10] if section else section}) or section_title({section_title})")
                    continue
                yield ParsedInfo(event='register_job', 
                                 data={'obj': {'title': goal_title}, 
                                       'section_title': section_title, 
                                       'section': section})

    def create_lines(self, content: str) -> iter:
        return self._create_lines(content)

    def _create_lines(self, content: str) -> iter:
        pattern = r'(성과목표\s*[ⅠⅡⅢⅣⅤV]-[1-5])(.*?)(?=성과목표\s*[ⅠⅡⅢⅣⅤV]-[1-5]|전략목표\s*[ⅠⅡⅢⅣⅤV]|Ⅳ\.\s*환류|Ⅳ\.\s*협업과제|$)'
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).findall(content)
