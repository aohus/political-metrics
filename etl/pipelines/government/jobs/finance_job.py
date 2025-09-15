import asyncio
import copy
import re
from dataclasses import dataclass
from enum import Enum


class FinanceBusinessProcessor:
    def __init__(self, parser, writer, *args, **kwargs):
        self.parser = parser
        self.writer = writer

    async def process(self, job):
        await self.process_lines(job)

    async def process_lines(self, job):
        data = None
        content = job.content
        data_class = job.data_class

        for matches in self.parser.parse_lines(content):
            stage, infos = await self.get_infos(matches)

            if stage == '주제' or data.stage:
                data = await self.create_data(data_class, data, stage)
            else:
                data = await self.update_data(data, stage, infos)
        await self.writer.add(data)

    async def get_infos(self, *matches):
        sep, title, f_title_code, f_subsidy, business_code, f_category = matches
        is_subsidy, stage = await self.get_stage(sep, business_code, f_subsidy)

        infos = {
            'title': title, 
            'finance_code': f_title_code, 
            'business_code': business_code, 
            'f_category': f_category
        }
        return stage, is_subsidy, infos

    async def update_data(self, data, infos: dict):
        data.update(**{k: v for k, v in infos.items() if v})

    async def create_data(self, data_class, data=None, stage=None):
        base_info = {}
        if stage:
            keys = {
                '프로그램': ('unit', 'sunit', 'details'),
                '단위사업': ('sunit', 'details'),
                '세부사업': ('details'),
            }
            base_info = {k: v for k, v in data.items() if k not in keys[stage]}

        asyncio.create_task(self.writer.write(data))
        data = data_class(**base_info)

    async def get_stage(self, sep: str, code: str, subsidy_info: str) -> tuple[bool, str]:
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
        return (line for line in txt.split('\n') if len(line) > 2)

    async def parse(self, content: str):
        lines = self.create_lines(content)
        for line in lines:
            for matches in self.compiler.finditer(line):
                yield matches

