import logging
import re
from dataclasses import dataclass

from base_processor import BaseNestedParser, BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class SubTaskSectionProcessor(BaseProcessor):
    pass 


class SubTaskNestedSectionParser(BaseParser):
    def __init__(self):
        self.compiler = re.compile(
            r'([^가-힣])\s*(\((.+?)\))?\s*(.+?)[^가-힣\d\w]?\n+(?=[^가-힣 ])', 
            re.DOTALL | re.IGNORECASE)

    def _create_lines(self, content: str):
        content = re.sub(r"\n[①②③④⑤⑥⑦⑧⑨⑩➊➋➌➍]", "\n①", content)
        return [content]
    
    def _parse(self, lines: list) -> iter:
        for line in lines:
            for matches in self.compiler.finditer(line):
                sep, _, title, content = matches.groups()
                content = content.replace('\n', ' ')
                if not content:
                    continue
                yield ParsedInfo(event='create_data', data={'sep': sep, 'title': title, 'content': content})
                # return sep, {'sep': sep, 'title': title, 'content': content}



# class NestedSectionParser:
#     def __init__(self):
#         self.infos = []
#         self.lines = []
#         self.map = set()
#         self.step = 0
#         self.max_step = 0
#         self.section_title = ""
    
#     def _get_initial_sep(self):
#         try:
#             return self.lines[0][0]
#         except:
#             print("no sections", self.lines)
    
#     def _get_line(self):
#         while True:
#             if self.step >= self.max_step:
#                 return 
            
#             line = self.lines[self.step]
#             if self._line_validation(line):
#                 return line
#             self.step += 1
            
#     def _line_validation(self, line):
#         return len(line) > 0
    
#     def process_line(self):
#         line = self._get_line()
#         if not line:
#             return "eof", {}
#         return self._process_line(line)

#     def _process_line(self, line):
#         pass
    
#     def _create_lines(self, section: str):
#         self.lines = [line for line in section.split('\n') if line]
#         self.max_step = len(self.lines)
    
#     def process(self, section):
#         self._create_lines(section)
#         self.nested_processor()
#         return self.infos
    
#     def nested_processor(self, last_stage_no: str = None, sep: str = None, map: set = set(), **info):
#         n = 0
#         if not sep:
#             sep = self._get_initial_sep()
#             map = {sep}

#         stage_map = copy.deepcopy(map)
#         stage_sep = cur_sep = sep
#         stage_map.add(cur_sep)
#         try:
#             while True:
#                 cur_sep, info = self.process_line()
#                 if cur_sep == 'eof':
#                     return 'eof', {}
                
#                 if cur_sep != stage_sep:
#                     if cur_sep not in stage_map:
#                         cur_sep, info = self.nested_processor(last_stage_no=stage_no, sep=cur_sep, map=stage_map, info=info)
#                         if cur_sep != stage_sep:
#                             return cur_sep, info
#                     else:
#                         return cur_sep, info
                
#                 n += 1
#                 stage_no = f'{last_stage_no}-{n}' if last_stage_no else str(n)
                
#                 info['no'] = stage_no
#                 self.infos.append(info)
#                 self.step += 1
#         except Exception as e:
#             print('info: ', info)
#             # print(self.step, last_stage_no, stage_sep, cur_sep, stage_map)


# # class FinanceNestedSectionParser(NestedSectionParser):
# #     def __init__(self):
# #         super().__init__()
# #         self.section_title = 'finance'
# #         self.subject_compiler = re.compile(r'(.+?)\s*(?:\(([^\)]*)\)$|(특별교부금|보통교부금)$|$)', re.DOTALL | re.IGNORECASE)
# #         self.business_compiler = re.compile((
# #             r'(^[^가-힣0-9\(’]?)\s*'
# #             r'(.*?)\s*'
# #             # r'(?:\(([^0-9]+?)\))?\s*'
# #             r'(?:\(([0-9\-]{3,8})\))?\s*'
# #             r'(?:\[(.+?)\])?\s*'
# #             r'(특별교부금|일반회계|일반재정|일반|특교|균특회계|균특|고특|고특회계|보통교부금|기금|$)'
# #             r'(특별교부금|일반회계|일반재정|일반|특교|균특회계|균특|고특|고특회계|보통교부금|기금|$)'
# #             r'(?:\s*\[(.+?)\])?\s*'
# #         ), re.DOTALL | re.IGNORECASE)
    
# #     def process(self, section):
# #         self._create_lines(section)
# #         self.nested_processor(sep='x')
# #         return self.infos
    
# #     def _create_lines(self, section: str):
# #         txt = re.sub(
# #             r'.*?단위\s*\s*\:.+?(?=\n)'
# #             r'|\n회계\s*구분.+?(?=\n)'
# #             r'|((\s계)?\s\(?[0-9\.\,\-]{1,8}|신규)\)?\s\(?[0-9\.\,\-]{1,8}\)?(?=\n)'
# #             r'|((\s계)?\s\(?[0-9]{1,5}\.[0-9]{1,2}\)?)'
# #             r'|\n[^가-힣]+?\n|\s*[0-9]\」', 
# #             '', section)
# #         txt = re.sub(r'\n(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금)\s*(?=\n)', '\\1', txt)
# #         txt = re.sub(r'\n\((.+?)\s*(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금)?\n?(.+?)\)', ' [\\1\\3] \\2', txt, re.DOTALL | re.IGNORECASE)
# #         txt = re.sub(r"\n[①②③④⑤⑥⑦⑧⑨⑩➊➋➌➍]", "\n①", txt)
# #         self.lines = [line for line in txt.split('\n') if len(line) > 2]
# #         self.max_step = len(self.lines)
    
# #     def _process_line(self, line: str) -> tuple[str, dict]:
# #         char = line[0]
# #         if ('\uac00' <= char <= '\ud7a3') or (char in '0123456789'):
# #             return self._process_subject(line)
# #         else:
# #             return self._process_business(line)
        
# #     def _process_subject(self, line: str):
# #         for match in self.subject_compiler.findall(line):
# #             subject, f_category_1, f_category_2 = match
# #             if match := re.match(r'([0-9]{4}$|[0-9]{4}-[0-9]{3}$)', f_category_1):
# #                 return 'x', {
# #                     'sep': 'x',
# #                     'name': subject, 
# #                     'code': match.group(1),
# #                     'detail': '',
# #                     'f_category': '',
# #                     'stage': '단위사업'
# #                 }
# #             return 'x', {
# #                 'sep': 'x',
# #                 'name': subject, 
# #                 'code': '',
# #                 'detail': '',
# #                 'f_category': f_category_1 if f_category_1 else f_category_2,
# #                 'stage': '주제'
# #             }

# #     def _process_business(self, line: str) -> tuple[str, dict]:
# #         stage = {
# #             3: '내역사업', 
# #             4: '단위사업', 
# #             8: '내역사업', 
# #             6: '내내역사업'
# #         }

# #         for match in self.business_compiler.findall(line):
# #             sep, bs_nm, code, detail, f_category, detail_list = match
# #             return sep, {
# #                 'sep': sep,
# #                 'name': bs_nm, 
# #                 'detail': detail if detail else detail_list.replace('내역: ', ''),
# #                 'code': code, 
# #                 'f_category': f_category,
# #                 'stage': stage.get(len(code)) if code else ''
# #             }

