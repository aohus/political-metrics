import logging
import re

from base_processor import BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class TargetParser(BaseParser):
    def __init__(self):
        self.compiler = re.compile(r"^(?:\s*\((.*?)\)\s*(.*?))$|^(?:(.*?)\s*[:：]\s*(.*?))$", re.DOTALL | re.IGNORECASE)

    def _create_lines(self, content: str):
        content = re.sub(r'\n', '', content)
        content = re.sub(r'[◦ㅇ]', 'ㅇ', content)
        return [line for line in content.split('ㅇ ') if len(line) > 5]

    def _parse(self, lines: list) -> iter:
        for line in lines:
            if matches := self.compiler.match(line):
                target_type_1, target_1, target_type_2, target_2 = matches.groups()
                target_type = target_type_1 or target_type_2
                target = target_1 or target_2
                yield ParsedInfo(event='create_data', data={'target_type': target_type, 'target': target})
            else:
                yield ParsedInfo(event='create_data', data={'target_type': '수혜자', 'target': line})