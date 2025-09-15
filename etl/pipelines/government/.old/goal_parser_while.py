import json
import os
import random
import re
from typing import Any, Callable, Dict, List, Optional

g = ["성과목표Ⅰ","성과목표Ⅱ","성과목표Ⅲ","성과목표Ⅳ","성과목표Ⅴ"]


class GoalCreator:
    GOAL_TEMPLATE = { # 성과목표Ⅰ (1) 주요 내용 ~ (5) 관리과제별 추진계획
        '성과목표': "",
        '외부환경 요인 및 갈등관리계획': [],
        '관리과제': [] #task list
    } 

    def __init__(self, lines):
        self.task_creater = TaskCreator()
        self.goals = []
        self.lines = lines 

    def search_goal_line(self):
        l = ""
        while self.lines:
            text = re.sub(r'[\s\-]', '', l)[0:5]
            while text not in g:
                if not self.lines:
                    break
                l = self.lines.pop(0)
                text = re.sub(r'[\s\-]', '', l)[0:5]
            print("text: ", l)
            goal = { # 성과목표Ⅰ (1) 주요 내용 ~ (5) 관리과제별 추진계획
                '성과목표': "",
                '외부환경 요인 및 갈등관리계획': [],
                '관리과제': [] #task list
            }
            goal['성과목표'] = l
            title = ""

            while self.lines and title not in ['외부환경요인및갈등관리계획', '외부환경갈등요인분석및갈등관리계획', '외부환경갈등요인분석및갈등관리계획']:
                l = self.lines.pop(0)
                title = ''.join(re.findall(r'[가-힣]+', l))
            
            while self.lines and title != '관리과제별추진계획':
                l = self.lines.pop(0)
                goal['외부환경 요인 및 갈등관리계획'].append(l)
                title = ''.join(re.findall(r'[가-힣]+', l))
                
            l, tasks = self.create_task()
            goal['관리과제'] = tasks
            self.goals.append(goal)

        return self.goals
        
    def create_task(self):
        return self.task_creater.parse_lines(self.lines)


class TaskCreator:
    # SECTION_MARKERS = {
    #     '□추진배경': 'background',
    #     '□추진배경(목적)': 'background', 
    #     '□주요내용및추진계획': 'content',
    #     '□수혜자및이해관계집단': 'target',
    #     "<’23년도과제추진계획>": 'plan',
    #     '□기대효과': 'effect',
    #     '□관련재정사업내역': 'finance',
    #     '': 'create_task'
    # }

    SECTION_MARKERS = {
        '□추진배경': 'background',
        '□추진배경목적': 'background', 
        '추진배경': 'background', 
        '추진배경목적': 'background', 
        '□주요내용및추진계획': 'content',
        '주요내용및추진계획': 'content',
        '□수혜자및이해관계집단': 'target',
        '수혜자및이해관계집단': 'target',
        "년도과제추진계획": 'plan',
        "<’24년도과제추진계획>": 'plan',
        '□기대효과': 'effect',
        '기대효과': 'effect',
        '□관련재정사업내역': 'finance',
        '관련재정사업내역': 'finance',
        '': 'create_task'
    }

    BREAK_PATTERNS = list(SECTION_MARKERS.keys()) + ['□수혜자체감도조사계획', '□성과지표', '□성과지표및측정방법']
    TASK_RANGE = ('\uf000', '\U000fffff')
    
    KOREAN_RANGE = ('\uac00', '\ud7a3')  # 한글 범위
    NUMBERS = '0123456789'


    def __init__(self):
        self.current_task: Optional[Dict] = None
        self.task_number = 0
        self.lines: List[str] = []
        self.cnt = 0
    
        
        # 종료 조건 패턴들 (추론된 값)
        self.termination_patterns = {"성과목표Ⅰ", "성과목표Ⅱ", "성과목표Ⅲ", "성과목표Ⅳ", "성과목표Ⅴ"}
        
        # 핸들러 매핑
        self.handlers: Dict[str, Callable] = {
            'background': self._handle_background,
            'content': self._handle_content, 
            'target': self._handle_target,
            'plan': self._handle_plan,
            'effect': self._handle_effect,
            'finance': self._handle_finance,
            'create_task': self._create_new_task
        }

    def parse_lines(self, lines: List[str]) -> List[Dict]:
        """메인 파싱 함수"""
        self.tasks = []
        self.lines = lines

        try:
            while self.lines:
                current_line = self._get_next_line()

                if handler_name := self._get_handler_for_line(current_line):
                    handler = self.handlers.get(handler_name)
                    if handler:
                        if handler_name == 'create_task':
                            handler(current_line)
                        else:
                            handler()
                if self._is_termination_condition(current_line):
                    return current_line, self.tasks
                    
        except Exception as e:
            print(e.with_traceback())
            
        if self.current_task:
            self.tasks.append(self.current_task.copy())
            
        return "", self.tasks

    def _get_next_line(self) -> str:
        return self.lines.pop(0) if self.lines else ""

    def _peek_next_line(self) -> str:
        return self.lines[0] if self.lines else ""

    def _get_handler_for_line(self, line: str) -> Optional[str]:
        _line = line.replace(' ', '')
        return self.SECTION_MARKERS.get(_line) or self.SECTION_MARKERS.get(_line[0])

    def _is_break_condition(self, line: str) -> bool:
        _line = line.replace(' ', '')
        return _line in self.BREAK_PATTERNS or _line[0] in self.BREAK_PATTERNS

    def _is_termination_condition(self, line: str) -> bool:
        cleaned_text = re.sub(r'[\s\-]', '', line)[:5]
        return cleaned_text in self.termination_patterns

    def _parse_section(self, processor_func: Callable[[str], None]) -> Optional[str]:
        while self.lines:
            line = self._get_next_line()

            if self._is_break_condition(line):
                break
            processor_func(line)

        if handler_name := self._get_handler_for_line(line):
            handler = self.handlers.get(handler_name)
            if handler:
                if handler_name == 'create_task':
                    handler(line)
                else:
                    handler()

    def _create_new_task(self, line):
        if self.current_task:
            self.tasks.append(self.current_task.copy())

        self.current_task = {
            '추진배경': [],
            '대상': {},
            '주요내용 및 추진계획': [],
            '과제추진계획': [],
            '재정사업': [],
            '기대효과': []
        }
        
        self.task_number += 1
        self.current_task['관리과제번호'] = self.task_number
        self.current_task['관리과제명'] = line
        
    def _handle_background(self):
        """추진배경 섹션 처리"""
        current_text = ""
        
        def process_background_line(line: str):
            nonlocal current_text
            if line.startswith('ㅇ'):
                if current_text:
                    self.current_task['추진배경'].append(current_text.strip())
                current_text = line[2:].strip()
            else:
                current_text += " " + line.strip()
        
        next_handle = self._parse_section(process_background_line)
        
        if current_text:
            self.current_task['추진배경'].append(current_text.strip())
        return next_handle

    def _handle_target(self):
        current_key = None
        
        def process_target_line(line: str):
            nonlocal current_key
            parts = re.compile(r"([ㅇㅇ∘◦]\s)\(?([수혜자이해관계집단]{2,7})\s*[:：\)]*\s(.*)").search(line)
            if parts:
                current_key = parts.group(2)
                if current_key in self.current_task['대상'].keys():
                    current_key = f'{current_key}_{random.random()}'
                self.current_task['대상'][current_key] = parts.group(3)
            else:
                if not current_key:
                    current_key = '수혜자'
                    self.current_task['대상'][current_key] = ""
                self.current_task['대상'][current_key] += line

        
        next_line = self._parse_section(process_target_line)
        return next_line
    
    def _handle_plan(self):
        """과제추진계획 섹션 처리"""
        def process_plan_line(line: str):
            if line.strip():
                self.current_task['과제추진계획'].append(line.strip())
        
        next_line = self._parse_section(process_plan_line)
        return next_line
    
    def _handle_content(self):
        """주요내용 섹션 처리 (가장 복잡한 로직)"""
        current_number = ""
        current_text = ""
        char_mapping: Dict[str, int] = {}
        status_counters: List[int] = []

        def process_content_line(line: str):
            nonlocal current_number, current_text
            
            if not line.strip():
                return
                
            first_char = line[0]
            
            # 한글이나 숫자가 아닌 경우 (구분자로 추정)
            if not (self.KOREAN_RANGE[0] <= first_char <= self.KOREAN_RANGE[1] or 
                   first_char in self.NUMBERS):
                
                # 이전 항목 저장
                if current_number and current_text:
                    self.current_task['주요내용 및 추진계획'].append({
                        '번호': current_number,
                        '내용': current_text.strip()
                    })
                
                # 새로운 번호 체계 생성
                if first_char in char_mapping:
                    step = char_mapping[first_char]
                    status_counters[step] += 1
                    # 하위 레벨 카운터 리셋
                    if step < len(status_counters) - 1:
                        for i in range(step + 1, len(status_counters)):
                            status_counters[i] = 0
                    current_number = '-'.join(str(i) for i in status_counters[:step + 1])
                else:
                    # 새로운 문자 등록
                    char_mapping[first_char] = len(char_mapping)
                    status_counters.append(1)
                    current_number = '-'.join(str(i) for i in status_counters)
                
                current_text = line.strip()
            else:
                # 기존 텍스트에 추가
                current_text += " " + line.strip()
        
        next_line = self._parse_section(process_content_line)
        
        # 마지막 항목 저장
        if current_number and current_text:
            self.current_task['주요내용 및 추진계획'].append({
                '번호': current_number,
                '내용': current_text.strip()
            })
        return next_line
    
    def _handle_finance(self):
        """재정사업 섹션 처리"""
        def process_finance_line(line: str):
            if line.strip():
                self.current_task['재정사업'].append(line.strip())
        
        next_line = self._parse_section(process_finance_line)
        return next_line
    
    def _handle_effect(self):
        """기대효과 섹션 처리"""
        current_text = ""
        
        def process_effect_line(line: str):
            nonlocal current_text
            if line.startswith('ㅇ'):
                if current_text:
                    self.current_task['기대효과'].append(current_text.strip())
                current_text = line[2:].strip()
            else:
                current_text += " " + line.strip()
        
        next_line = self._parse_section(process_effect_line)
        
        if current_text:
            self.current_task['기대효과'].append(current_text.strip())
        return next_line
    
    def _handle_unknown_section(self, line: str):
        """알 수 없는 섹션 처리"""
        print(f"알 수 없는 섹션: {line}")

    def reset(self):
        """파서 상태 초기화"""
        self.tasks = []
        self.current_task = None
        self.task_number = 0
        self.lines = []


class TaskParserOld:
    SECTION_MARKERS = {
        '□추진배경': 'background',
        '□추진배경목적': 'background', 
        '추진배경': 'background', 
        '추진배경목적': 'background', 
        '□주요내용및추진계획': 'content',
        '주요내용및추진계획': 'content',
        '□수혜자및이해관계집단': 'target',
        '수혜자및이해관계집단': 'target',
        "년도과제추진계획": 'plan',
        "<’24년도과제추진계획>": 'plan',
        '□기대효과': 'effect',
        '기대효과': 'effect',
        '□관련재정사업내역': 'finance',
        '관련재정사업내역': 'finance',
        '': 'create_task'
    }
    re.compile(r'(□?\s*추진배경|□?\s*주요\s*내용|□?\s*수혜자|□?\s*기대\s*효과|□?\s*관련\s*재정|년도\s*과제\s*추진\s*계획)(.*?)(?=□?\s*추진배경|□?\s*주요\s*내용|□?\s*수혜자|□?\s*기대\s*효과|□?\s*관련\s*재정|년도\s*과제\s*추진\s*계획)')
    BREAK_PATTERNS = list(SECTION_MARKERS.keys()) + ['□수혜자체감도조사계획', '□성과지표', '□성과지표및측정방법']
    TASK_RANGE = ('\uf000', '\U000fffff')

    KOREAN_RANGE = ('\uac00', '\ud7a3')  # 한글 범위
    NUMBERS = '0123456789'

    def __init__(self):
        self.current_task: Optional[Dict] = None
        self.task_number = 0
        self.lines: List[str] = []

        self.handlers: Dict[str, Callable] = {
            'background': self._handle_background,
            'content': self._handle_content, 
            'target': self._handle_target,
            'plan': self._handle_plan,
            'effect': self._handle_effect,
            'finance': self._handle_finance,
            'create_task': self._create_new_task
        }

    def parse(self, lines: List[str]) -> List[Dict]:
        self.tasks = []
        self.lines = lines

        try:
            while self.lines:
                current_line = self._get_next_line()

                if handler_name := self._get_handler_for_line(current_line):
                    handler = self.handlers.get(handler_name)
                    if handler:
                        if handler_name == 'create_task':
                            handler(current_line)
                        else:
                            handler()
                    
        except Exception as e:
            print(e.with_traceback())
            
        if self.current_task:
            self.tasks.append(self.current_task.copy())
            
        return "", self.tasks

    def _get_next_line(self) -> str:
        return self.lines.pop(0) if self.lines else ""

    def _peek_next_line(self) -> str:
        return self.lines[0] if self.lines else ""

    def _get_handler_for_line(self, line: str) -> Optional[str]:
        _line = line.replace(' ', '')
        return self.SECTION_MARKERS.get(_line) or self.SECTION_MARKERS.get(_line[0])

    def _is_break_condition(self, line: str) -> bool:
        _line = line.replace(' ', '')
        return _line in self.BREAK_PATTERNS or _line[0] in self.BREAK_PATTERNS

    def _parse_section(self, processor_func: Callable[[str], None]) -> Optional[str]:
        while self.lines:
            line = self._get_next_line()

            if self._is_break_condition(line):
                break
            processor_func(line)

        if handler_name := self._get_handler_for_line(line):
            handler = self.handlers.get(handler_name)
            if handler:
                if handler_name == 'create_task':
                    handler(line)
                else:
                    handler()

    def _create_new_task(self, line):
        if self.current_task:
            self.tasks.append(self.current_task.copy())

        self.current_task = {
            '추진배경': [],
            '대상': {},
            '주요내용 및 추진계획': [],
            '과제추진계획': [],
            '재정사업': [],
            '기대효과': []
        }
        
        self.task_number += 1
        self.current_task['관리과제번호'] = self.task_number
        self.current_task['관리과제명'] = line
        
    def _handle_background(self):
        """추진배경 섹션 처리"""
        current_text = ""
        
        def process_background_line(line: str):
            nonlocal current_text
            if line.startswith('ㅇ'):
                if current_text:
                    self.current_task['추진배경'].append(current_text.strip())
                current_text = line[2:].strip()
            else:
                current_text += " " + line.strip()
        
        next_handle = self._parse_section(process_background_line)
        
        if current_text:
            self.current_task['추진배경'].append(current_text.strip())
        return next_handle

    def _handle_target(self):
        current_key = None
        
        def process_target_line(line: str):
            nonlocal current_key
            parts = re.compile(r"([ㅇㅇ∘◦]\s)\(?([수혜자이해관계집단]{3,7})\s*[:：\)]*\s(.*)").search(line)
            if parts:
                current_key = parts.group(2)
                if current_key in self.current_task['대상'].keys():
                    current_key = f'{current_key}_{random.random()}'
                self.current_task['대상'][current_key] = parts.group(3)
            else:
                if not current_key:
                    current_key = '수혜자'
                    self.current_task['대상'][current_key] = ""
                self.current_task['대상'][current_key] += line

        
        next_line = self._parse_section(process_target_line)
        return next_line
    
    def _handle_plan(self):
        """과제추진계획 섹션 처리"""
        def process_plan_line(line: str):
            if line.strip():
                self.current_task['과제추진계획'].append(line.strip())
        
        next_line = self._parse_section(process_plan_line)
        return next_line
    
    def _handle_content(self):
        """주요내용 섹션 처리 (가장 복잡한 로직)"""
        current_number = ""
        current_text = ""
        char_mapping: Dict[str, int] = {}
        status_counters: List[int] = []

        def process_content_line(line: str):
            nonlocal current_number, current_text
            
            if not line.strip():
                return
                
            first_char = line[0]
            
            # 한글이나 숫자가 아닌 경우 (구분자로 추정)
            if not (self.KOREAN_RANGE[0] <= first_char <= self.KOREAN_RANGE[1] or 
                   first_char in self.NUMBERS):
                
                # 이전 항목 저장
                if current_number and current_text:
                    self.current_task['주요내용 및 추진계획'].append({
                        '번호': current_number,
                        '내용': current_text.strip()
                    })
                
                # 새로운 번호 체계 생성
                if first_char in char_mapping:
                    step = char_mapping[first_char]
                    status_counters[step] += 1
                    # 하위 레벨 카운터 리셋
                    if step < len(status_counters) - 1:
                        for i in range(step + 1, len(status_counters)):
                            status_counters[i] = 0
                    current_number = '-'.join(str(i) for i in status_counters[:step + 1])
                else:
                    # 새로운 문자 등록
                    char_mapping[first_char] = len(char_mapping)
                    status_counters.append(1)
                    current_number = '-'.join(str(i) for i in status_counters)
                
                current_text = line.strip()
            else:
                # 기존 텍스트에 추가
                current_text += " " + line.strip()
        
        next_line = self._parse_section(process_content_line)
        
        # 마지막 항목 저장
        if current_number and current_text:
            self.current_task['주요내용 및 추진계획'].append({
                '번호': current_number,
                '내용': current_text.strip()
            })
        return next_line
    
    def _handle_finance(self):
        """재정사업 섹션 처리"""
        # "(단위",
        # "회계구분",

        # "", " 특별교부금", "▪ 특별교부금", "- 특별교부금"
        # "", " ① 특별교부금"
        # "이름(특별교부금 이름)", " ▪ (00) 특교"
        # "이름(Ⅰ일반재정②)", "① 이름(0000) 일반회계 ", "▪ 이름(0000-000) 일반회계" or "이름(000)"
        # "(", 로 시작하는 것 제외, 'n」' 제외

        def process_finance_line(line: str):
            cp = re.compile(r'([^가-힣\(’]?)\s*([^0-9\()]*)(\((.*?)\))?', re.DOTALL | re.IGNORECASE)
            if line:
                match = cp.findall(line)
                match[1]
                match[2]
                match[3]
                self.current_task['재정사업'].append(line.strip())
        
        next_line = self._parse_section(process_finance_line)
        return next_line
    
    def _handle_effect(self):
        """기대효과 섹션 처리"""
        current_text = ""
        
        def process_effect_line(line: str):
            nonlocal current_text
            if line.startswith('ㅇ'):
                if current_text:
                    self.current_task['기대효과'].append(current_text.strip())
                current_text = line[2:].strip()
            else:
                current_text += " " + line.strip()
        
        next_line = self._parse_section(process_effect_line)
        
        if current_text:
            self.current_task['기대효과'].append(current_text.strip())
        return next_line
    
    def _handle_unknown_section(self, line: str):
        """알 수 없는 섹션 처리"""
        print(f"알 수 없는 섹션: {line}")

    def reset(self):
        """파서 상태 초기화"""
        self.tasks = []
        self.current_task = None
        self.task_number = 0
        self.lines = []


# if __name__ == '__main__':
#     doc_parser = GoalDocParser('2022')
#     doc_parser.parse_goals()


if __name__ == '__main__':
    year = '2022'
    with open(f'/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/부처별/교육부/교육부성과관리시행계획{year}.txt', 'r') as f:
        txt = f.read()
    lines = re.sub(r'[\uf000-\U000fffff]', '\uf000', txt).split('\n')
    lines = [ line for line in lines if line ]

    creator = GoalCreator(lines)
    goals = creator.search_goal_line()
    
    with open(f'/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/부처별/교육부/교육부성과관리시행계획{year}_t.json', 'w', encoding='utf-8') as f:
        json.dump(goals, f, ensure_ascii=False, indent=4)



        # task = Task(title=title, no=self.task_num)

        # for match in self.compilers.get('task').finditer(content):
        #     section_title = match.group('section_title')
        #     section = match.group('section_content')
        #     if not section:
        #         print("no section", task.title, self.task_num, section_title)
        #     self.parse_section(task, section_title, section)
        # self.tasks.append(task)

    # def parse_section(task, section_title, section):
    #     self.section_manager.add(task, section_title, section)



# class TaskParser:
#     def __init__(self):
#         self.tasks = []
#         self.task_num = 0
#         self.section_manager = section_manager
#         self._parser_configs = {
#             'target': self._parse_section_target,
#             'background': self._parse_section_background,
#             'finance': self._parse_section_finance,
#             'effect': self._parse_section_effect,
#             'plan': self._parse_section_plan,
#             'subtasks': self._parse_section_subtasks
#         }
#         c = re.compile(r'([ㅇ◦]\s*.+?)(?=ㅇ|◦|$)', re.DOTALL | re.IGNORECASE)
#         self.compilers = {
#             'task_list': re.compile(
#                 r'[\uf000-\U000fffff]\s*(?P<task_title>.{1,50})'
#                 r'(\([ⅠⅡⅢⅣⅤ1234567①②③④⑤⑥⑦⑧⑨⑩\-]+?\))'
#                 r'\n(?P<task_content>□?\s*추진\s*배경.+?)'
#                 r'(?=[\uf000-\U000fffff]\s*.{1,50}□?\s*추진\s*배경|Ⅳ\s|$)'
#                 , re.DOTALL | re.IGNORECASE),
#             'task': re.compile(
#                 r'□?\s*(?P<section_title>추진\s*배경\s*.*?|주요\s*내용.*?|수혜자\s*및.*?|기대\s*효과.*?|관련\s*재정.*?|[1-9]{0,2}\s*년도\s*과제\s*추진\s*계획.*?)'
#                 r'\n(?P<section_content>.*?)'
#                 r'(?=추진\s*배경|(?:□\s*)주요\s*내용\s*및|[^\(]수혜자\s*및|성과지표\s*및|수혜자\s*체감도|기대\s*효과|관련\s*재정|[1-3]{0,2}\s*년도\s*과제\s*추진\s*계획|$)'
#                 , re.DOTALL | re.IGNORECASE),
#             'background': c,
#             'target': c,
#             'effect': c,
#         }

#     def parse(self, goal: str):
#         """
#         성과목표(goal)에서 '관리과제'(task) 리스트 추출
#         성과목표Ⅰ-1 [① 관리과제, ... , ⑥ 관리과제]
#         """
#         try:
#             for match in self.compilers.get('task_list').finditer(goal):
#                 task_title = match.group('task_title')
#                 task_content = match.group('task_content')
#                 self.parse_task(task_title, task_content)
#             return self.tasks_to_dict()
#         except Exception as e:
#             print(e)
#             print("Task List ", self.task_num)

#     def tasks_to_dict(self):
#         return [task.to_dict() for task in self.tasks]
                        
#     def parse_task(self, title: str, content: str):
#         """
#         '관리과제(task)의 주요 정보(section)' 추출
#         Ⅰ-1-① : [배경, 대상, 주요내용(사업 리스트), 계획, 재정사업, 기대효과]
#         """
#         self.task_num += 1
#         task = Task(title=title, no=self.task_num)

#         for match in self.compilers.get('task').finditer(content):
#             section_title = match.group('section_title')
#             section = match.group('section_content')
#             if not section:
#                 print("no section", task.title, self.task_num, section_title)
#             # self.parse_section(task, section_title, section)
#             self.parse_section(task, section_title, section)
#         self.tasks.append(task)

#     def parse_section(task, section_title, section):
#         self.section_manager.add(task, section_title, section)


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
