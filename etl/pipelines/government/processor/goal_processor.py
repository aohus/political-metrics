import logging
import re

import base_processor
from base_processor import ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class GoalProcessor(base_processor.BaseProcessor):    
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
            r'((?:\([3-5]\))\s*(외부\s*환경|기타|관리\s*과제).*?\n)'
            r'(.+?)'
            r'(?=(?:\([3-5]\))\s*(?:기타|관리과제별\s*추진계획)|$)', 
            re.DOTALL | re.IGNORECASE
        )
        self._founded = []

    def parse(self, content):
        lines = self.create_lines(content)
        for matches in lines:
            goal_num, goal_title, line = matches.groups()
            self._founded.append(goal_num)
            for match in self.compiler.finditer(line):
                _, section_title, section = match.groups()
                if not self._is_validate(goal_title, section_title, section):
                    continue
                yield ParsedInfo(event='register_job', 
                                 data={'obj': {'no': goal_num, 'title': goal_title}, 
                                       'section_title': section_title, 
                                       'section': section})
        logger.info(f'Parse Goal Completed! Founded: {len(self._founded)}, GoalNums: {self._founded}')

    def create_lines(self, content: str) -> iter:
        return self._create_lines(content)

    def _create_lines(self, content: str) -> iter:
        clean_content = self._clean_text(content)
        pattern = r'(성과목표\s*[ⅠⅡⅢⅣⅤV]-[1-5])\s*(.*?)\n(.+?)(?=성과목표\s*[ⅠⅡⅢⅣⅤV]-[1-5]|전략목표\s*[ⅠⅡⅢⅣⅤV]|Ⅳ\.\s*환류|Ⅳ\.\s*협업과제|$)'
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).finditer(clean_content)

    def _clean_text(self, content):
        clean_content = re.sub(r'[\`\’\'\‘]', '’', content)
        clean_content = re.sub(r'[\‧\ㆍ\·]', '·', clean_content)
        clean_content = re.sub(r'[\▪\￭]', '▪', clean_content)
        clean_content = re.sub(r'[\」]', '｣', clean_content)
        clean_content = re.sub(r'[\「]', '｢', clean_content)
        clean_content = re.sub(r'[\∼]', '~', clean_content)
        clean_content = re.sub(
            r'\n구\s*분\s*추\s*진\s*계\s*획\s*세\s*부\s*일\s*정\s*(비\s*고)?'
            r'|[1-4]/4\s*분기\s*'
            r'|\([가-힣\, ]*?\s*단위\s*\:.+?\)'
            r'|\s*회계\s*구분.+?\n'
            r'|\s*(?!\d)\d[\｣]',
            '', clean_content)
        clean_content = re.sub(r'\n[①②③④⑤⑥⑦⑧⑨⑩⑪➀➁➂➃➄➅❶❷❸❹➊➋➌➍➎➏]', '\n●', clean_content)
        clean_content = re.sub(r'\nㅇ', '\n◎', clean_content)
        # clean_content = re.sub(r'[\⇒\→\⇨]', '→', clean_content)
        return clean_content

    def _is_validate(self, goal_title, section_title, section):
        if not section_title or len(section) < 20:
            logger.error(f"goal_title: '{goal_title}' has no section({section.replace('\n', '')}) or section_title({section_title})")
            return False
        return True
