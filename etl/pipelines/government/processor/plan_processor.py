import logging
import re

from base_processor import BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class PlanParser(BaseParser):
    def __init__(self):
        self.compiler = re.compile(r'(.*?)\s([\’\‘\'\~\.\s0-9년월]*?|계속|연중)(\s.*?|$)')

    def _create_lines(self, content: str):
        content = re.sub(r'구 분 추진계획 세부일정 비 고(\n)?|[1-4]/4\s*분기\s*(\n)?', '', content)
        content = re.sub(r'\n(\’[0-9].*?[0-9]{1,2}월|[0-9\~]{1,12}월~?|계속|연중)(?:\n)', '\\1\n', content)
        return content.split('\n')

    def _parse(self, lines: list) -> iter:
        for line in lines:
            for matches in self.compiler.finditer(line):
                content, plan_at, extra = matches.groups()
                if not content:
                    logger.error(f'plan - content not found: matches {matches.groups()}, \nline: {line}')
                    continue
                yield ParsedInfo(event='create_data', data={'content': content, 'plan_at': plan_at, 'extra': extra})
