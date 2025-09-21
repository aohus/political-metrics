import logging
import re

from base_processor import BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class TaskProcessor(BaseProcessor):
    def _process_data(self, parsed):
        title = parsed.data.get('section_title')
        parsed.data['job_type'] = self._get_job_type(title)
        return (parsed.event, parsed.data)

    def _get_job_type(self, title: str):
        job_map = {
            '추진': 'background',
            '주요': 'subtasks',
            '수혜': 'target',
            '기대': 'effect',
            '관련': 'finance',
            '년도': 'plan',
            '22': 'plan',
            '23': 'plan',
            '24': 'plan',
        }
        if title[0:2] in job_map.keys():
            return job_map.get(title[0:2])


class TaskParser(BaseParser):
    def __init__(self):
        self.compiler = re.compile(
            r'□?\s*(?P<section_title>추진\s*배경\s*.*?|주요\s*내용.*?|수혜자\s*및.*?|기대\s*효과.*?|관련\s*재정.*?|[1-9]{0,2}\s*년도\s*과제\s*추진\s*계획.*?)'
            r'\n(?P<section_content>.*?)'
            r'(?=(?:□\s*)추진\s*배경|주요\s*내용\s*및|[^\(]수혜자\s*및|이해관계자\s등|성과지표\s*및|수혜자\s*체감도|기대\s*효과|관련\s*재정|[1-9]{0,2}\s*년도\s*과제\s*추진\s*계획|$)'
            , re.DOTALL | re.IGNORECASE)

    def _create_lines(self, content: str):
        """
        성과목표(goal)에서 '관리과제'(task) 리스트 추출
        성과목표Ⅰ-1 [① 관리과제, ... , ⑥ 관리과제]
        """
        pattern = (
            r'[\uf000-\U000fffff]\s*(?P<task_title>.{1,100})'
            r'(?:\(([ⅠⅡⅢⅣⅤ1234567①②③④⑤⑥⑦⑧⑨⑩\-]+?)\))'
            r'\n(?P<task_content>□?\s*추진\s*배경.+?)'
            r'(?=[\uf000-\U000fffff]\s*.{1,100}□?\s*추진\s*배경|Ⅳ\s|$)'
        )
        return re.compile(pattern, re.DOTALL | re.IGNORECASE).finditer(content)

    def parse(self, content: str):
        """
        '관리과제(task)의 주요 정보(section)' 추출
        Ⅰ-1-① : [배경, 대상, 주요내용(사업 리스트), 계획, 재정사업, 기대효과]
        """
        lines = self.create_lines(content)
        for line in lines:
            title, no, section = line.groups()
            title = title.replace('\n', '')
            for section_title, section in self.compiler.findall(section):
                if not section or len(section) < 20:
                    logger.error(f"task title: '{title}' has no section({section[0:10] if section else section}), section_title({section_title})")
                    continue
                yield ParsedInfo(event='register_job', 
                                 data={'obj': {'title': title, 'no': no},
                                       'section_title': section_title, 
                                       'section': section})
