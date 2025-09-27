import logging
import re

from base_processor import BaseParser, BaseProcessor, ParsedInfo

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class PlanParser(BaseParser):
    def __init__(self):
        self.compiler = re.compile(r'^\s*(.+?)[ \n]([\d월\.\~\-]{1,12}[월\.](?!\d)~?|계속|수시|연중|매월|매주|매일|지속|미정|$)(.*?)$', re.DOTALL)

    def _create_lines(self, content: str):
        sep = '\n'
        if re.match(r'[^\w\(\’\[\｢\「]', content[0]):
            sep = sep + content[0]
        content = '\n' + content
        content = re.sub(r'\~?\’2\d\.', '', content)
        content = re.sub(r'\n[1-4]/4|\n분기', '\n', content)
        content = re.sub(r'\n([\d월\.\~\-]{1,12}[월\.]~?|[1-4]/4분기|상반기|하반기|계속|수시|연중|매월|매주|매일|지속|미정)(?=\n)', ' \\1\n', content)
        return [line for line in content.split(sep) if line]

    def _parse(self, lines: list) -> iter:
        for line in lines:
            content, plan_at, extra = self._parse_detail(line)
            yield ParsedInfo(event='create_data', data={'content': content, 'plan_at': plan_at, 'extra': extra})
    
    def _parse_detail(self, line):
        matches = self.compiler.match(line)
        if not matches:
            matches = re.compile(r'^\s*(.+?)[ \n]([1-4]분기|상반기|하반기)\s*(\w*?)$', re.DOTALL).match(line)
        
        if matches:
            content, plan_at, extra = matches.groups()
            extra = extra.replace('\n', '')
            if extra and re.match(r'\w', extra[0]):
                content, extra = content + ' ' + extra, ''

            content = content.replace('\n', '')
            return content, plan_at, extra
        return line[1:], '', ''
                
