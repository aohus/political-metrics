import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import pandas as pd
from utils.file.fileio import read_file

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """법률안 문서 정보를 담는 데이터 클래스"""
    title: str = ""
    bill_number: str = ""
    proposal_date: str = ""
    submission_date: str = ""
    is_alternative: bool = False
    alternative_bill_numbers: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    full_text: str = ""

    def to_json(self) -> Dict[str, Any]:
        """JSON 직렬화"""
        return {
            "title": self.title,
            "bill_number": self.bill_number,
            "proposal_date": self.proposal_date,
            "submission_date": self.submission_date,
            "is_alternative": self.is_alternative,
            "alternative_bill_numbers": self.alternative_bill_numbers,
            "sections": self.sections,
            "full_text": self.full_text,
        }


class DocumentParser:
    def __init__(
        self,
        data_saver=None,
        max_concurrent: int = 10,
    ):
        self.data_saver = data_saver if data_saver else None
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 정규표현식 패턴들
        self.patterns = {
            # 기존 패턴들
            "proposal_date": re.compile(
                r"발의연월일\s*:\s*([0-9]{4}\.\s*[0-9]{1,2}\.\s*[0-9]{1,2}\.?)",
                re.IGNORECASE,
            ),
            "submission_date": re.compile(
                r"제안연월일\s*:\s*([0-9]{4}\.\s*[0-9]{1,2}\.\s*[0-9]{1,2}\.?)",
                re.IGNORECASE,
            ),
            "is_alternative": re.compile(r"\(대안\)", re.IGNORECASE),
            "alternative_section": re.compile(
                r"1\.\s*대안의\s*제안경위(.*?)(?=2\.\s*대안의\s*제안이유|$)",
                re.DOTALL | re.IGNORECASE,
            ),
            "bill_number_int": re.compile(r"\b([1-9][0-9]{3,7})\b"),
            "bill_number_str": re.compile(r"제([1-9][0-9]{3,7})호"),
            "sections": {
                "제안이유": re.compile(
                    r"제안이유\s*(.*?)(?=주요내용|법률\s*제|참고사항|$)",
                    re.DOTALL | re.IGNORECASE,
                ),
                "주요내용": re.compile(
                    r"주요내용\s*(.*?)(?=법률\s*제|신[·•․ㆍ]\s*구조문대비표|참고사항|$)",
                    re.DOTALL | re.IGNORECASE,
                ),
                "제안이유_및_주요내용": re.compile(
                    r"제안이유\s*및\s*주요내용\s*(.*?)(?=법률\s*제|참고사항|$)",
                    re.DOTALL | re.IGNORECASE,
                ),
                "참고사항": re.compile(
                    r"참고사항\s*(.*?)(?=법률\s*제|$)",
                    re.DOTALL | re.IGNORECASE,
                ),
                "법률_제_호": re.compile(
                    r"법률\s*제\s*\d*\s*호\s*(.*?)(?=신[·•․ㆍ]\s*구조문대비표|부\s*칙|$)",
                    re.DOTALL | re.IGNORECASE,
                ),
                "부칙": re.compile(
                    r"부\s*칙\s*(.*?)(?=신[·•․ㆍ]\s*구조문대비표|$)", re.DOTALL | re.IGNORECASE
                ),
                "신구조문대비표": re.compile(
                    r"(신[·•․ㆍ]\s*구조문대비표.*?)(?=부\s*칙|$)", re.DOTALL | re.IGNORECASE
                ),
            },
        }

    async def parse(self, text_dir: str, batch_size=20, **kwargs) -> list[DocumentInfo]:
        """디렉토리 내 모든 파일에서 법률안 정보 추출"""
        if len(text_dir) > batch_size:
            results = await self.extract_multiple_files_batched(text_dir, batch_size)
        else:
            results = await self.extract_multiple_files(text_dir)
        return results

    def parse_info(self, text: str, title: str) -> DocumentInfo:
        """텍스트에서 법률안 정보 추출 (동기 처리 - 정규식 처리는 빠름)"""
        info = DocumentInfo(full_text=text, title=title)
        info.bill_number = title.split("_")[0]

        proposal_date_match = self.patterns["proposal_date"].search(text)
        if proposal_date_match:
            info.proposal_date = proposal_date_match.group(1).strip()

        submission_date_match = self.patterns["submission_date"].search(text)
        if submission_date_match:
            info.submission_date = submission_date_match.group(1).strip()

        info.is_alternative = bool(self.patterns["is_alternative"].search(info.title))
        if info.is_alternative:
            info.alternative_bill_numbers = self._extract_alternative_bill_numbers(text)

        info.sections = self._extract_sections(text)
        return info

    def _clean_escape(self, text: str) -> str:
        """텍스트에서 이스케이프 문자 제거"""
        return re.sub(r'(?<!\.)\n', '', text)
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """full_text에서 주요 섹션들을 추출"""
        sections = {}

        for section_name, pattern in self.patterns["sections"].items():
            match = pattern.search(text)
            if match:
                content = match.group(1).strip()
                if section_name in ["제안이유", "주요내용", "제안이유_및_주요내용"]:
                    content = self._clean_escape(content)
                if content:
                    sections[section_name] = content

        if "제안이유_및_주요내용" in sections:
            del sections["제안이유"], sections["주요내용"]
        return sections

    def _extract_alternative_bill_numbers(self, text: str) -> List[str]:
        """대안 제안경위에서 7자리 의안번호들 추출"""
        alternative_numbers = []

        # "1. 대안의 제안경위" 섹션 찾기
        alternative_section_match = self.patterns["alternative_section"].search(text)

        if alternative_section_match:
            section_text = alternative_section_match.group(1)
            section_text = section_text.replace("\n", " ")
            alter_nums = self.patterns["bill_number_str"].findall(section_text)
            alter_nums += self.patterns["bill_number_int"].findall(section_text)
            alternative_numbers = list(set(alter_nums))
            filtered = [n for n in alternative_numbers if not re.search(rf"{n}\.", section_text)]
        return filtered

    def _extract_comparison_table(self, text: str) -> str:
        """신·구조문대비표 추출"""
        table_start_pos = None

        for pattern in self.patterns["comparison_table_patterns"]:
            match = pattern.search(text)
            if match:
                table_start_pos = match.start()
                break

        if table_start_pos is None:
            return ""

        content_match = self.patterns["comparison_content"].search(text)

        if content_match:
            table_text = content_match.group(1)
        else:
            table_text = text[table_start_pos:]
        return table_text

    async def extract_from_file(self, file_path: Union[str, Path]) -> DocumentInfo:
        async with self.semaphore:
            try:
                title = file_path.split("/")[-1].split(".")[0]
                text_result = await read_file(file_path)
                return self.parse_info(text_result, title)
            except Exception as e:
                return e

    async def extract_multiple_files(
        self, file_paths: List[Union[str, Path]]
    ) -> list[DocumentInfo]:
        """비동기 여러 파일에서 정보 추출"""
        tasks = [self.extract_from_file(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리된 결과들을 적절히 변환
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(str(result))
            else:
                processed_results.append(result)
        return processed_results

    async def extract_multiple_files_batched(
        self, dir_path: str, batch_size: int = 50
    ) -> list[DocumentInfo]:
        """배치 단위로 여러 파일에서 정보 추출 (대용량 처리용)"""
        save_tasks = []
        file_paths = [os.path.join(dir_path, fname) for fname in os.listdir(dir_path)]
        logger.info(f"총 {len(file_paths)}개의 파일")

        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            batch_results = await self.extract_multiple_files(batch)
            save_tasks.append(
                asyncio.create_task(self.data_saver.bulk_save(batch_results))
            )
            # 배치 간 짧은 휴식
            if i + batch_size < len(file_paths):
                await asyncio.sleep(0.1)

        results = []
        completed_count, total_bills, success_bills = 0, 0, 0

        for task in asyncio.as_completed(save_tasks):
            try:
                result = await task
                results.append(result)
                completed_count += 1
                total_bills += result.get("total_items")
                success_bills += result.get("success_count")
            except Exception as e:
                print(f"❌ 태스크 에러: {e}")
                results.append(None)
                completed_count += 1
            print(
                f"✅ 변환된 의안: ({total_bills}, {success_bills}), 태스크 완료 ({completed_count}/{len(save_tasks)})"
            )


async def parse_doc(file_path: str) -> DocumentInfo:
    """비동기 단일 파일에서 법률안 정보 추출"""
    parser = DocumentParser()
    info = await parser.extract_from_file(file_path)
    return info


async def parse_multiple_docs(
    file_paths: List[str], data_saver, max_concurrent: int = 10, batch_size: int = 50
) -> list[DocumentInfo]:
    """비동기 여러 파일에서 법률안 정보 추출"""
    parser = DocumentParser(data_saver=data_saver, max_concurrent=max_concurrent)

    if len(file_paths) > batch_size:
        results = await parser.extract_multiple_files_batched(file_paths, batch_size)
    else:
        results = await parser.extract_multiple_files(file_paths)
    return results
