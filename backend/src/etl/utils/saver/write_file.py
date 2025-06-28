"""
비동기 PDF 텍스트 파일 저장기
PDF 텍스트 추출 결과를 다양한 형식으로 비동기 저장
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFTextFileSaver:
    """PDF 텍스트 추출 결과를 다양한 형식으로 비동기 저장하는 클래스"""

    def __init__(
        self,
        output_dir: str = "bill_pdf_parser/extracted_texts",
        max_concurrent: int = 10,
    ):
        """
        Args:
            output_dir: 저장할 디렉토리 경로
            max_concurrent: 동시 처리 수 제한
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def _get_safe_filename(self, filename: str) -> str:
        """파일명에서 특수문자 제거"""
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", filename)
        safe_name = re.sub(r"\s+", "_", safe_name)
        return safe_name

    def _get_timestamp(self) -> str:
        """현재 시간을 파일명용 문자열로 반환"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    async def save(
        self,
        data: Any,
        filename: Optional[str] = None,
        add_timestamp: bool = False,
        indent: int = 2,
    ) -> str:
        """JSON 형식으로 비동기 저장"""
        async with self.semaphore:
            try:

                def serialize_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(
                        f"Object of type {type(obj)} is not JSON serializable"
                    )

                # data.section = asdict(data.sections)
                result = asdict(data)
                json_content = json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=indent,
                    default=serialize_datetime,
                )

                if not filename:
                    filename = (
                        result.get("title")
                        if result.get("title")
                        else f"bill_{time.time()}"
                    )

                file_path = f"{str(self.output_dir)}/{filename}.json"
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(json_content)

                logger.info(f"JSON 파일 저장 완료: {file_path}")
                return str(file_path)

            except Exception as e:
                logger.error(f"JSON 파일 저장 실패: {e}")
                raise

    async def save_text(
        self,
        text_content: str,
        filename: str,
        add_timestamp: bool = True,
    ) -> str:
        """일반 텍스트 형식으로 비동기 저장"""
        async with self.semaphore:
            safe_filename = self._get_safe_filename(filename)

            if add_timestamp:
                safe_filename = f"{safe_filename}_{self._get_timestamp()}"

            file_path = self.output_dir / f"{safe_filename}.txt"

            try:
                async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                    await f.write(text_content)

                logger.info(f"텍스트 파일 저장 완료: {file_path}")
                return str(file_path)

            except Exception as e:
                logger.error(f"텍스트 파일 저장 실패: {e}")
                raise

    async def batch_save(self, data_list: List[Any]):
        results = []
        tasks = [self.save(data) for data in data_list]

        # 모든 저장 작업을 동시 실행
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 정리
        for result in completed_tasks:
            if isinstance(result, Exception):
                logger.error(f"저장 실패: {result}")
            else:
                results.append(result)
        return results

    async def bulk_save(self, data_list: List[Any], batch_size: int = 10):
        results = {}
        success_count = 0
        failed_count = 0

        # 배치 단위로 처리
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i : i + batch_size]
            batch_num = i // batch_size + 1

            try:
                batch_results = await self.batch_save(batch)
                success_count += len(batch_results)
                results[f"batch_{batch_num}"] = batch_results

                if i + batch_size < len(data_list):
                    await asyncio.sleep(0.1)

            except Exception as e:
                failed_count += len(batch)
                results[f"batch_{batch_num}"] = {"error": str(e)}
            logger.info(f"저장 성공: {success_count}, 실패: {failed_count}")
        return {
            "total_items": len(data_list),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }


async def save_extraction_log(
    pdf_path: str,
    extraction_results: Dict[str, Any],
    output_dir: str = "extracted_texts",
) -> str:
    """추출 과정의 로그를 비동기 저장"""
    log_path = Path(output_dir) / "extraction_log.txt"

    # 부모 디렉토리 생성
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_content = []
    log_content.append("=" * 80)
    log_content.append(f"추출 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_content.append(f"PDF 파일: {pdf_path}")
    log_content.append(
        f"추출 방법: {extraction_results.get('extraction_method', 'N/A')}"
    )
    log_content.append(
        f"문자 수: {extraction_results.get('statistics', {}).get('total_characters', 0):,}"
    )
    log_content.append(
        f"성공 여부: {'성공' if 'error' not in extraction_results else '실패'}"
    )

    if "error" in extraction_results:
        log_content.append(f"오류 내용: {extraction_results['error']}")

    log_content.append("=" * 80 + "\n")

    async with aiofiles.open(log_path, "a", encoding="utf-8") as f:
        await f.write("\n".join(log_content))

    return str(log_path)


async def batch_process_and_save(
    data_list: List[Any],
    output_dir: str = "batch_extracted_texts",
    save_formats: List[str] = None,
    max_concurrent: int = 10,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """대량 데이터를 배치 단위로 비동기 저장"""
    if save_formats is None:
        save_formats = ["json", "text"]

    saver = PDFTextFileSaver(output_dir, max_concurrent)

    results = {}
    success_count = 0
    failed_count = 0

    # 배치 단위로 처리
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i : i + batch_size]
        batch_num = i // batch_size + 1

        try:
            batch_filename = f"batch_{batch_num:04d}"
            batch_results = await saver.save_multiple_formats(
                batch, batch_filename, save_formats
            )

            # 성공한 파일 수 계산
            for format_type, file_paths in batch_results.items():
                success_count += len(file_paths)

            results[f"batch_{batch_num}"] = batch_results

            # 배치 간 짧은 휴식
            if i + batch_size < len(data_list):
                await asyncio.sleep(0.1)

        except Exception as e:
            failed_count += len(batch)
            results[f"batch_{batch_num}"] = {"error": str(e)}

    return {
        "total_items": len(data_list),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
    }


async def save_multiple_bills_async(
    bill_infos: List[Any], output_dir: str = "bills_output", max_concurrent: int = 15
) -> Dict[str, Any]:
    """여러 법률안 정보를 비동기로 저장"""
    saver = PDFTextFileSaver(output_dir, max_concurrent)

    # 동시 저장 작업 생성
    tasks = []
    for i, bill_info in enumerate(bill_infos):
        filename = f"bill_{bill_info.bill_number}_{i+1:04d}"
        task = saver.save(bill_info, filename, add_timestamp=False)
        tasks.append(task)

    # 모든 작업을 동시 실행
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 정리
    saved_files = []
    errors = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append(f"bill_{i+1}: {result}")
        else:
            saved_files.append(result)

    return {
        "total_bills": len(bill_infos),
        "saved_count": len(saved_files),
        "error_count": len(errors),
        "saved_files": saved_files,
        "errors": errors,
    }


def create_saver(
    output_dir: str = "./bill_pdf_parser/extracted_texts", max_concurrent: int = 10
) -> PDFTextFileSaver:
    """비동기 PDF 저장기 생성 팩토리 함수"""
    return PDFTextFileSaver(output_dir, max_concurrent)
