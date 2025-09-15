import re
from dataclasses import dataclass
from enum import Enum

from .base_job import NestedSectionParser, Result


class SubTaskSectionData:
    pass


class SubTaskSection:
    pass


class SubTaskNestedSectionParser(NestedSectionParser):
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
