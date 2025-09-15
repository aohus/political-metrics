import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .section import FinanceSectionParser, SubTasksNestedSectionParser


class EtcParser:
    def parse(self, content: str):
        return content


class RiskManageParser:
    def parse(self, content: str):
        return content


@dataclass
class Task:
    title: str
    no: int
    background: list = None
    subtasks: list = None
    plan: list = None
    target: list = None
    finance: list = None
    effect: list = None

    def to_dict(self):
        return {
            '관리과제명': self.title,
            '관리과제번호': self.no,
            '추진배경': self.background,
            '주요내용 및 추진계획': self.subtasks,
            '과제추진계획': self.plan,
            '대상': self.target,
            '관련재정사업': self.finance,
            '기대효과': self.effect,
        }


class TaskParser:
    def __init__(self):
        self.tasks = []
        self.task_num = 0
        self.section_manager = section_manager
        self._parser_configs = {
            'target': self._parse_section_target,
            'background': self._parse_section_background,
            'finance': self._parse_section_finance,
            'effect': self._parse_section_effect,
            'plan': self._parse_section_plan,
            'subtasks': self._parse_section_subtasks
        }
        c = re.compile(r'([ㅇ◦]\s*.+?)(?=ㅇ|◦|$)', re.DOTALL | re.IGNORECASE)
        self.compilers = {
            'task_list': re.compile(
                r'[\uf000-\U000fffff]\s*(?P<task_title>.{1,50})'
                r'(\([ⅠⅡⅢⅣⅤ1234567①②③④⑤⑥⑦⑧⑨⑩\-]+?\))'
                r'\n(?P<task_content>□?\s*추진\s*배경.+?)'
                r'(?=[\uf000-\U000fffff]\s*.{1,50}□?\s*추진\s*배경|Ⅳ\s|$)'
                , re.DOTALL | re.IGNORECASE),
            'task': re.compile(
                r'□?\s*(?P<section_title>추진\s*배경\s*.*?|주요\s*내용.*?|수혜자\s*및.*?|기대\s*효과.*?|관련\s*재정.*?|[1-9]{0,2}\s*년도\s*과제\s*추진\s*계획.*?)'
                r'\n(?P<section_content>.*?)'
                r'(?=추진\s*배경|(?:□\s*)주요\s*내용\s*및|[^\(]수혜자\s*및|성과지표\s*및|수혜자\s*체감도|기대\s*효과|관련\s*재정|[1-3]{0,2}\s*년도\s*과제\s*추진\s*계획|$)'
                , re.DOTALL | re.IGNORECASE),
            'background': c,
            'target': c,
            'effect': c,
        }

    def parse(self, goal: str):
        """
        성과목표(goal)에서 '관리과제'(task) 리스트 추출
        성과목표Ⅰ-1 [① 관리과제, ... , ⑥ 관리과제]
        """
        try:
            for match in self.compilers.get('task_list').finditer(goal):
                task_title = match.group('task_title')
                task_content = match.group('task_content')
                self.parse_task(task_title, task_content)
            return self.tasks_to_dict()
        except Exception as e:
            print(e)
            print("Task List ", self.task_num)

    def tasks_to_dict(self):
        return [task.to_dict() for task in self.tasks]
                        
    def parse_task(self, title: str, content: str):
        """
        '관리과제(task)의 주요 정보(section)' 추출
        Ⅰ-1-① : [배경, 대상, 주요내용(사업 리스트), 계획, 재정사업, 기대효과]
        """
        self.task_num += 1
        task = Task(title=title, no=self.task_num)

        for match in self.compilers.get('task').finditer(content):
            section_title = match.group('section_title')
            section = match.group('section_content')
            if not section:
                print("no section", task.title, self.task_num, section_title)
            # self.parse_section(task, section_title, section)
            self.parse_section(task, section_title, section)
        self.tasks.append(task)

    def parse_section(task, section_title, section):
        self.section_manager.add(task, section_title, section)


    # def parse_section(self, task, section_title, section):
    #     parser = self._get_parser(section_title)
    #     parser(task, section)

    # def _get_parser(self, section_title):
    #     title = self._get_title(section_title)
    #     # if title == 'subtasks':
    #     if parser := self._parser_configs.get(title):
    #         return parser
    #     else:
    #         print("title ", section_title)
        
    # def _get_title(self, section_title):
    #     section_map = {
    #         '추진': 'background',
    #         '주요': 'subtasks',
    #         '수혜': 'target',
    #         '기대': 'effect',
    #         '관련': 'finance',
    #         '년도': 'plan',
    #         '22': 'plan',
    #         '23': 'plan',
    #         '24': 'plan',
    #     }
    #     return section_map.get(section_title.replace(' ', '')[:2]) if not None else ""

    # def _parse_section_target(self, task, section: str): 
    #     task.target = self.compilers.get('target').findall(section)

    # def _parse_section_background(self, task, section: str): 
    #     task.background = self.compilers.get('background').findall(section)

    # def _parse_section_effect(self, task, section: str): 
    #     task.effect = self.compilers.get('effect').findall(section)
    
    # def _parse_section_plan(self, task, section: str): 
    #     task.plan = [line for line in section.split('\n') if line]
    
    # def _parse_section_finance(self, task, section: str): 
    #     parser = FinanceSectionParser()
    #     task.finance = parser.process(section)

    # def _parse_section_subtasks(self, task, section: str): 
    #     parser = SubTasksNestedSectionParser()
    #     task.subtasks = parser.process(section)
