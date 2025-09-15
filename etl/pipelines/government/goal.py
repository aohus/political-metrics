import json
import re
from dataclasses import dataclass

from .task import EtcParser, RiskManageParser, TaskParser


class Status:
    pass


@dataclass
class Goal:
    year: str
    ministry: str
    goal_num: str
    goal: str

    def to_dict(self):
        return {
            '사업연도': self.year,
            '소관': self.ministry,
            '성과목표번호': self.goal_num,
            '성과목표': self.goal,
        }

class GoalManager:
    def __init__(self, goal_parser):
        self.goals = []
        self.goal_parser = goal_parser

    def add(self, year, ministry, goal_list):
        for goal_num, content in goal_list:
            goal_num = goal_num.replace(' ', '')
            goal = Goal(year=year, ministry=ministry, goal_num=goal_num, goal=goal)
            self.goal_parser.parse(goal, content)
            self.goals.append(goal)
class GoalManager:
    def __init__(self, goal_parser):
        self.goals = []
        self.goal_parser = goal_parser

    def add(self, year, ministry, goal_list):
        for goal_num, content in goal_list:
            goal_num = goal_num.replace(' ', '')
            goal = Goal(year=year, ministry=ministry, goal_num=goal_num, goal=goal)
            self.goal_parser.parse(goal, content)
            self.goals.append(goal)


class GoalParser:
    def __init__(self):
        self.compiler = re.compile(
            r'((?:\([1-9]\))\s*(?:외부환경.*?갈등관리계획|기타|관리과제별\s*추진계획))'
            r'(.*?)'
            r'(?=(?:\([1-9]\))\s*(?:기타|관리과제별\s*추진계획)|$)', 
            re.DOTALL | re.IGNORECASE
        )
        # self._parser_config = {
        #     'etc': EtcParser(),
        #     'task': TaskParser(),
        #     'risk_manage': RiskManageParser()
        # }

    def parse(self, goal, content):
        self.extract_all_sections(goal, content)

    def extract_all_sections(self, goal, section_text: str) -> dict[str, str]:
        risk_manage_parser = RiskManageParser()
        etc_parser = EtcParser()
        task_parser = TaskParser()

        matches = self.combined_compiler.findall(section_text)
        for match in matches:
            title = match[0]
            content = match[1]

            if '외부환경' in title:
                goal, 
                goal.risk_manage = risk_manage_parser.parse(content)
            elif '기타' in title:
                goal.etc = etc_parser.parse(content)
            elif '관리과제' in title:
                goal.tasks = task_parser.parse(content)
            else:
                raise


class GoalDocParser:
    def __init__(self, goal_manager, goal_factory, goal_parser):
        self.goals = []
        self.goal_manager = goal_manager(goal_factory, goal_parser)

    def _load_doc(self, filepath: str):
        # with open(f'/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/교육부_전략_과제_{filepath}.json', 'r') as f:
        #     yearly_tasks = json.load(f)

        # goals = {}
        # for 전략목표 in yearly_tasks:
        #     전략목표번호 = 전략목표['전략목표'][0]
        #     for 성과목표, 관리과제 in 전략목표['성과목표'].items():
        #         성과목표번호 = f'{전략목표번호}-{성과목표[0]}'
        #         성과목표전체 = f'{전략목표번호}-{성과목표}'
        #         goals[성과목표번호] = [title for title in 관리과제['관리과제']]

        with open(filepath, 'r') as f:
            return f.read()

    def get_doc_info(self, filepath):
        ministry = filepath.split('/')[-2]
        year = filepath.split('_')[2][:4]
        text = self._load_doc(filepath)
        return year, ministry, text

    def parse_goals(self, filepath):
        year, ministry, text = self.get_doc_info(filepath)
        compiler = re.compile(r'(성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5])(.*?)(?=성과목표\s*[ⅠⅡⅢⅣⅤ]-[1-5]|전략목표\s*[ⅠⅡⅢⅣⅤ]|$)', re.DOTALL | re.IGNORECASE)
        goal_list = compiler.findall(text)
        self.goal_manager.add(year, ministry, goal_list)


def run():
    year = '2022'
    ministry = '교육부'
    basedir = '/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/부처별'
    filepath = f'{basedir}/{ministry}/성과관리시행계획_{ministry}_{year}.txt'
    goal_parser = GoalParser()
    doc_parser = GoalDocParser(
        goal_parser, lambda year, goal_num, ministry: Goal(year=year, goal_num=goal_num, ministry=ministry)
    )    
    doc_parser.parse_goals(filepath)


if __name__ == '__main__':
    run()
