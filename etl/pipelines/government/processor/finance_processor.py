import logging
import re

from base_processor import BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class FinanceBusinessProcessor(BaseProcessor):
    def _process_data(self, is_subsidy, subject, finance_code, items) -> tuple:
        if is_subsidy:
            data = self._make_subsidy_obj(subject, finance_code, items)
        else:
            data = self._make_general_obj(subject, finance_code, items)
        if not data:
            print(subject, items)
        return ('create_data_many', data)

    def _make_subsidy_obj(self, subject, finance_code, items):
        return [{
            'subject': subject,
            'finance_code': finance_code,
            'program': '지방교육재정교부금',
            'unit': '보통교부금' if '보통' in finance_code else '특별교부금',
            'items': items
        }]

    def _init_obj(self, base_obj, stage=None):
        level = {'program': 1, 'unit': 2, 'sunit': 3}
        if stage: 
            base_obj = {k: v for k, v in base_obj.items() if level.get(k, 0) < level.get(stage)}

        return {
            'subject': base_obj.get('subject'),
            'finance_code': base_obj.get('finance_code'),
            'program': base_obj.get('program'),
            'unit': base_obj.get('unit'),
            'sunit': base_obj.get('sunit'),
            'items': [],
            'extra': [],
        }

    def _make_general_obj(self, subject, finance_code, items) -> list:
        objs = []
        if not items:
            return self._make_subsidy_obj(subject, finance_code, items)

        obj = self._init_obj({'subject': subject, 'finance_code': finance_code})
        for sep, content, code, category in items:
            stage = self._get_stage(sep, code)

            if stage in ('items', 'extra'):
                obj[stage].append(content)
                continue 

            if obj.get(stage):
                objs.append(obj.copy())
                obj = self._init_obj(obj)
            else:
                obj[stage] = content
        objs.append(obj)
        return objs

    def _get_stage(self, sep, code):
        if code:
            return self._get_code_stage(code)
        return self._get_sep_stage(sep)
    
    def _get_sep_stage(self, sep):
        sep_map = {'(': 'items', '◎': 'unit', '▪': 'sunit'}
        return sep_map.get(sep, 'extra')

    def _get_code_stage(self, code):
        map = {10: 'program', 4: 'unit', 3: 'sunit', 2: 'items'}
        if '-' in code:
            code = code.split('-')[-1]
        code_len = len(code)
        if code_len == 4 and code[2:4] == '00':
            code_len = 10
        return map.get(code_len)

    def _get_subsidy_stage(self, code):
        map = {2: 'ssunit', 3: 'sssunit'}
        code_len = len(code.split('-'))
        return map.get(code_len)


class FinanceBusinessParser(BaseParser):
    def __init__(self):
        self.subject_compiler = re.compile(r'(.+?)(?:\((.*?)\)|$)', re.DOTALL | re.IGNORECASE)
        self.item_compiler = re.compile((
            r'\n?(?:([^가-힣0-9’]))\s*'
            r'(.*?)\s*'
            r'(?:\(([0-9\-]{3,13})\))?\s*' 
            r'(특별교부금|보통교부금|특교|교육특별|[가-힣\s]*회계|일반재정|일반|[가-힣]특|[가-힣\s]*기금)?'
            r'(?=\n|$)'
        ), re.DOTALL | re.IGNORECASE)

    def create_lines(self, content: str):
        return self._create_lines(content)

    def _create_lines(self, content: str):
        txt = re.sub(
            r'\n(특별교부금|보통교부금|특교|[가-힣]*회계|일반재정|일반|[가-힣]특|[가-힣]*기금|국고\(출연금\)|국고|지방비|출연금)?([^가-힣]*?)(?=\n)'
            r'|\n(\d/4|분기\s)'
            r'|(\s계)?\s([0-9\.\,\-\s신규]{1,}|\([0-9\.\,\-\s신규]{1,}\)\s\([0-9\.\,\-\s신규]{1,}\))(?=\n)'
            r'|\n([ⅠⅡⅢⅣⅤV]-[1-5]-[①②③④⑤⑥⑦⑧⑧⑨⑩⑪]\s*)',
            '', content)
        if txt[0] != '\n':
            txt = '\n' + txt

        lines = re.compile(r'(\n[가-힣a-zA-Z]{1,}.*?)(?=\n[가-힣a-zA-Z]|$)', re.DOTALL | re.IGNORECASE).findall(txt)
        if not lines:
            logger.error(f'Not matched line: {txt}')
            return [txt]
        return lines

    def _parse(self, lines: list) -> iter:
        for line in lines:
            data = self._parse_detail(line)
            yield ParsedInfo(event='process_data', data=data)
    
    def _parse_detail(self, line: str):
        is_subsidy = True if '특교' in line or '교부금' in line else False
        try:
            lines = line.split('\n')
            if len(lines) < 3:
                subject = lines[1]
                items = ""
            else: 
                _, subject, items = line.split('\n', 2)
            subject, finance_code = self.subject_compiler.findall(subject)[0]

            item_list = []   
            for item in self.item_compiler.finditer(items):
                item_list.append(item.groups())
        except Exception as e:
            print(e)
            print(line)

        return {
            'subject': subject,
            'finance_code': finance_code,
            'is_subsidy': is_subsidy,
            'items': item_list
        }    
