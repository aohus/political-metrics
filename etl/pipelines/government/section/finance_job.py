import copy
import re
from dataclasses import dataclass
from enum import Enum

from .base_job import Processor


class FinanceBusinessProcessor(Processor):
    def __init__(self, parser, obj_cls, **kwargs):
        self.parser = parser
        self.obj_cls = obj_cls
        self.year: str = kwargs.get('year')
        self.ministry: str = kwargs.get('ministry')

    def __call__(self, content: str, *args, **kwds):
        self.process(content=content)

    def insert(self, obj, *data):
        stage, infos = self.get_infos(data)

        if stage == '주제' or obj.get(stage):
            obj = self.create_obj(obj, stage)

        for key, data in infos.items():
            obj.set(key, data)

    def get_infos(self, *data):
        sep, title, f_title_code, f_subsidy, business_code, f_category = data
        is_subsidy, stage = self.get_stage(sep, business_code, f_subsidy)

        infos = {
            'title': title, 
            'finance_code': f_title_code, 
            'business_code': business_code, 
            'f_category': f_category
        }
        return stage, is_subsidy, infos

    def create_obj(self, obj=None, stage=None):
        base_info = {}
        if stage:
            keys = {
                '프로그램': ('unit', 'sunit', 'details'),
                '단위사업': ('sunit', 'details'),
                '세부사업': ('details'),
            }
            base_info = {k: v for k, v in obj.items() if k not in keys[stage]}

        obj = self.obj_cls(**base_info)
        self.obj_list.append(obj)

    def get_stage(self, sep: str, code: str, subsidy_info: str) -> tuple[bool, str]:
        is_subsidy = True if subsidy_info else False

        if sep == '(':
            return is_subsidy, '내내역사업'
        if sep == '※':
            return is_subsidy, '비고'
    
        if not (sep and code):
            return is_subsidy, '주제'
        
        if sep and not code:
            return None, '내역사업'
          
        match = re.match(r'([0-9]-[0-9\-]{1,5})|([0-9]{3,4}[0-9\-]{0,12})', code)
        subsidy_code, general_code = match[0], match[1]

        if subsidy_code:
            return self._get_subsidy_stage(subsidy_code)
        return self._get_general_stage(general_code)

    def _get_general_stage(self, code):
        map = {10: (0, '프로그램'), 4: (0, '단위사업'), 3: (0, '세부사업'), 2: (0, '내역사업')}
        code_len = len(code.split('-')[-1])
        if code_len == 4 and code[2:4] == '00':
            code_len = 10
        return map.get(code_len)

    def _get_subsidy_stage(self, code):
        map = {2: (1, '내내역사업'), 3: (1, '내내내역사업')}
        code_len = len(code.split('-')[-1])
        return map.get(code_len)


class FinanceBusinessParser:
    def __init__(self):
        self.compiler = re.compile((
            r'(^[^가-힣0-9\(’]?)\s*'
            r'(.*?)\s*'
            r'(?:\(([0-9\-]{3,8})\))?\s*'
            r'(?:\[(.+?)\])?\s*'
            r'(특별교부금|일반회계|일반재정|일반|특교|균특회계|균특|고특|고특회계|보통교부금|기금|$)'
            r'(특별교부금|일반회계|일반재정|일반|특교|균특회계|균특|고특|고특회계|보통교부금|기금|$)'
            r'(?:\s*\[(.+?)\])?\s*'
        ), re.DOTALL | re.IGNORECASE)

    def _create_lines(self, content: str):
        txt = re.sub(
            r'.*?단위\s*\s*\:.+?(?=\n)'
            r'|\n회계\s*구분.+?(?=\n)'
            r'|((\s계)?\s\(?[0-9\.\,\-]{1,8}|신규)\)?\s\(?[0-9\.\,\-]{1,8}\)?(?=\n)'
            r'|((\s계)?\s\(?[0-9]{1,5}\.[0-9]{1,2}\)?)'
            r'|\n[^가-힣]+?\n|\s*[0-9]\」', 
            '', content)
        txt = re.sub(r'\n(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금)\s*(?=\n)', '\\1', txt)
        txt = re.sub(r'\n\((.+?)\s*(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금)?\n?(.+?)\)', ' [\\1\\3] \\2', txt, re.DOTALL | re.IGNORECASE)
        txt = re.sub(r"\n[①②③④⑤⑥⑦⑧⑨⑩➊➋➌➍]", "\n①", txt)
        self.lines = [line for line in txt.split('\n') if len(line) > 2]

    def _process_lines(self, line: str) -> tuple[str, dict]:
        return self.compiler.finditer(line)


class CategoryType(Enum):
    GENERAL = "일반"
    SPECIAL = "특별회계"
    FUND = "기금"


@dataclass
class FinanceBusiness:
    year: str = ""
    ministry: str = ""
    subject: str = ""
    category: CategoryType = CategoryType.GENERAL
    finance_code: str = ""
    subsidy_code: str = ""
    program: str = ""
    unit: str = ""
    sunit: str = ""
    ps: str = ""

    def to_dict(self):
        return {
            '사업연도': self.year,
            '소관': self.ministry,
            '주제': self.subject,
            '회계구분': self.category,
            '회계코드': self.finance_code,
            '프로그램명': self.program,
            '단위사업명': self.unit,
            '내역사업명': self.sunit,
            '비고': self.ps,
            '내내역사업목록': self.ssunit,
        }


class NestedSectionParser:
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
            # print(self.step, last_stage_no, stage_sep, cur_sep, stage_map)


# class FinanceNestedSectionParser(NestedSectionParser):
#     def __init__(self):
#         super().__init__()
#         self.section_title = 'finance'
#         self.subject_compiler = re.compile(r'(.+?)\s*(?:\(([^\)]*)\)$|(특별교부금|보통교부금)$|$)', re.DOTALL | re.IGNORECASE)
#         self.business_compiler = re.compile((
#             r'(^[^가-힣0-9\(’]?)\s*'
#             r'(.*?)\s*'
#             # r'(?:\(([^0-9]+?)\))?\s*'
#             r'(?:\(([0-9\-]{3,8})\))?\s*'
#             r'(?:\[(.+?)\])?\s*'
#             r'(특별교부금|일반회계|일반재정|일반|특교|균특회계|균특|고특|고특회계|보통교부금|기금|$)'
#             r'(특별교부금|일반회계|일반재정|일반|특교|균특회계|균특|고특|고특회계|보통교부금|기금|$)'
#             r'(?:\s*\[(.+?)\])?\s*'
#         ), re.DOTALL | re.IGNORECASE)
    
#     def process(self, section):
#         self._create_lines(section)
#         self.nested_processor(sep='x')
#         return self.infos
    
#     def _create_lines(self, section: str):
#         txt = re.sub(
#             r'.*?단위\s*\s*\:.+?(?=\n)'
#             r'|\n회계\s*구분.+?(?=\n)'
#             r'|((\s계)?\s\(?[0-9\.\,\-]{1,8}|신규)\)?\s\(?[0-9\.\,\-]{1,8}\)?(?=\n)'
#             r'|((\s계)?\s\(?[0-9]{1,5}\.[0-9]{1,2}\)?)'
#             r'|\n[^가-힣]+?\n|\s*[0-9]\」', 
#             '', section)
#         txt = re.sub(r'\n(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금)\s*(?=\n)', '\\1', txt)
#         txt = re.sub(r'\n\((.+?)\s*(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금)?\n?(.+?)\)', ' [\\1\\3] \\2', txt, re.DOTALL | re.IGNORECASE)
#         txt = re.sub(r"\n[①②③④⑤⑥⑦⑧⑨⑩➊➋➌➍]", "\n①", txt)
#         self.lines = [line for line in txt.split('\n') if len(line) > 2]
#         self.max_step = len(self.lines)
    
#     def _process_line(self, line: str) -> tuple[str, dict]:
#         char = line[0]
#         if ('\uac00' <= char <= '\ud7a3') or (char in '0123456789'):
#             return self._process_subject(line)
#         else:
#             return self._process_business(line)
        
#     def _process_subject(self, line: str):
#         for match in self.subject_compiler.findall(line):
#             subject, f_category_1, f_category_2 = match
#             if match := re.match(r'([0-9]{4}$|[0-9]{4}-[0-9]{3}$)', f_category_1):
#                 return 'x', {
#                     'sep': 'x',
#                     'name': subject, 
#                     'code': match.group(1),
#                     'detail': '',
#                     'f_category': '',
#                     'stage': '단위사업'
#                 }
#             return 'x', {
#                 'sep': 'x',
#                 'name': subject, 
#                 'code': '',
#                 'detail': '',
#                 'f_category': f_category_1 if f_category_1 else f_category_2,
#                 'stage': '주제'
#             }

#     def _process_business(self, line: str) -> tuple[str, dict]:
#         stage = {
#             3: '내역사업', 
#             4: '단위사업', 
#             8: '내역사업', 
#             6: '내내역사업'
#         }

#         for match in self.business_compiler.findall(line):
#             sep, bs_nm, code, detail, f_category, detail_list = match
#             return sep, {
#                 'sep': sep,
#                 'name': bs_nm, 
#                 'detail': detail if detail else detail_list.replace('내역: ', ''),
#                 'code': code, 
#                 'f_category': f_category,
#                 'stage': stage.get(len(code)) if code else ''
#             }


class SubTasksNestedSectionParser(NestedSectionParser):
    def __init__(self):
        super().__init__()
        self.section_title = 'subtasks'
        self.subtasks_compiler = re.compile(r'([^가-힣])\s*(\((.+?)\))?\s*(.+?)[^가-힣\d\w]?\n+(?=[^가-힣 ])', re.DOTALL | re.IGNORECASE)

    def _create_lines(self, section: str):
        section = re.sub(r"\n[①②③④⑤⑥⑦⑧⑨⑩➊➋➌➍]", "\n①", section)
        self.lines = self.subtasks_compiler.findall(section)
        self.max_step = len(self.lines)
        
    def _process_line(self, line: tuple) -> tuple[str, str]:
        sep, _, title, content = line
        content = content.replace('\n', ' ')
        return sep, {'sep': sep, 'title': title, 'content': content}

