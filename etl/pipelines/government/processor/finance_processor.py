import asyncio
import logging
import re

from base_processor import BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class FinanceBusinessProcessor(BaseProcessor):
    def _update_data(self, parsed_data: dict, obj: dict):
        completed_obj, obj = self._update_obj(obj, parsed_data)
        
        if completed_obj and not completed_obj.get('subject'):
            logger.error(f"error completed: {completed_obj}")
        
        if completed_obj:
            completed_obj.pop('last')
        return completed_obj, obj

    def _create_new_obj(self, obj, stage, infos):
        keys = {
            'program': ('last', 'subject', 'finance_code', 'category', 'subsidy_code'),
            'unit': ('last', 'subject', 'finance_code', 'category', 'subsidy_code', 'program'),
            'sunit': ('last', 'subject', 'finance_code', 'category', 'subsidy_code', 'program', 'unit'),
        }
        if not stage:
            print(obj, stage, infos)
        new_obj = {k: v for k, v in obj.items() if k in keys[stage]}
        new_obj.update({k: v for k, v in infos.items() if v and not new_obj.get(k)})
        return obj, new_obj

    def _update_obj(self, obj, parsed_data):
        if parsed_data == "eof":
            return obj, {}
        
        sep, subject, finance_code, content, business_code, f_category = parsed_data.get('matches')
        if subject:
            new_obj = self._make_subject_obj(subject, finance_code)
            return obj, new_obj
        
        return self._make_stage_obj(obj, sep, content, business_code, f_category)

    def _make_subject_obj(self, subject, finance_code):
        new_obj = {
            'last': ('subject', ''),
            'subject': subject,
            'finance_code': finance_code,
        }
        
        if finance_code and not ('일반' in finance_code):
            new_obj['category'] = '지방교육재정교부금'
            new_obj['program'] = '지방교육재정교부금'
            new_obj['unit'] = '보통교부금' if '보통' in finance_code else '특별교부금'
            new_obj['sunit'] = finance_code
        return new_obj

    def _make_stage_obj(self, obj, sep, content, business_code, f_category) -> tuple[bool, str]:
        stage = None
        infos = {}
        if not obj.get('last'):
            print(obj, sep, content, business_code)
        last_stage, last_sep = obj.get('last')

        if f_category in ('특교', '특별교부금', '보통교부금', '교부금') and obj.get('program') is None:
            obj['category'] = '지방교육재정교부금'
            obj['program'] = '지방교육재정교부금'
            obj['unit'] = '보통교부금' if '보통' in f_category else '특별교부금'

        if sep == '(':
            stage = 'ssunit'
        if sep not in ('(', '▪', '①', '-'):
            stage = 'extra'
        if sep and not business_code:
            if last_sep != sep:
                stage = self._get_next_stage(last_stage)
                obj['last'] = (stage, sep)
            elif last_stage in ('subject', 'program', 'unit', 'sunit'):
                return self._create_new_obj(obj, last_stage, {last_stage: content})
            else:
                stage = last_stage

        if business_code:
            match = re.match(r'([0-9]-[0-9\-]{1,5})|(.*?[0-9]{3,4}$|.*?[0-9]{2,4}$)', business_code)
            subsidy_code, general_code = match[1], match[2]

            if subsidy_code:
                stage = self._get_subsidy_stage(subsidy_code)
                infos['subsidy_code'] = subsidy_code
            else:
                stage = self._get_general_stage(business_code)

        if stage in ('ssunit', 'sssunit', 'extra'):
            if not obj.get(stage):
                obj[stage] = []
            obj[stage].append(content)
            return None, obj

        if obj.get(stage):
            return self._create_new_obj(obj, stage, {stage: content})
        else:
            obj[stage] = content
            return None, obj

    def _get_next_stage(self, stage):
        next_stage = {
            'subject': 'ssunit',
            'program': 'unit',
            'unit': 'sunit',
            'sunit': 'ssunit',
            'ssunit': 'sssunit',
            'sssunit': 'extra',
            'extra': 'extra',
        }
        return next_stage[stage]

    def _get_general_stage(self, code):
        map = {10: 'program', 4: 'unit', 3: 'sunit', 2: 'ssunit'}
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
        self.compiler = re.compile((
            r'^(?:([^가-힣0-9’])|(.*?)(?:\((.*?)\)|$))\s*'  # 제목 or 맨 앞 특수문자
            r'(.*?)\s*' # '( ) or [ ] or 회계구분 ' 직전 내용
            r'(?:\(([0-9\-]{3,13})\))?\s*' 
            r'(특별교부금|일반회계|일반|일반재정|특교|균특회계|균특|고특|고특회계|기금|$)'
        ), re.DOTALL | re.IGNORECASE)

    def create_lines(self, content: str):
        return self._create_lines(content)

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
        txt += "\neof"
        return (line for line in txt.split('\n') if len(line) > 2)

    def _parse(self, lines: list) -> iter:
        for line in lines:
            if line != 'eof':
                for matches in self.compiler.finditer(line):
                    yield ParsedInfo(event='update_data', data={'matches': matches.groups()})
            else:
                yield ParsedInfo(event='update_data', data='eof')

