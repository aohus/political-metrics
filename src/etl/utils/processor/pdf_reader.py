"""
비동기 PDF 텍스트 추출기
여러 PDF 라이브러리를 사용한 고성능 비동기 텍스트 추출
"""

import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 필요한 라이브러리들 확인
try:
    import PyPDF2

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("PyPDF2가 설치되지 않았습니다: pip install PyPDF2")

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("pdfplumber가 설치되지 않았습니다: pip install pdfplumber")

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("PyMuPDF가 설치되지 않았습니다: pip install PyMuPDF")

try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams

    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    print("pdfminer가 설치되지 않았습니다: pip install pdfminer.six")


class PDFTextCleaner:
    """PDF에서 추출한 텍스트 정리 도구 (동기 처리 유지)"""

    def __init__(self, pdf_type: str = "bill"):
        self.pdf_type = pdf_type

    def clean(self, text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        return self._clean_page_num(text)

    def _clean_excape(self, text: str) -> str:
        # 연속된 개행 정리
        return re.sub(r"\n\s*\n", "\n\n", text)

    def _clean_space(self, text: str) -> str:
        # 불필요한 공백 제거
        return re.sub(r"\s+", " ", text)

    def _clean_page_num(self, text: str) -> str:
        # 페이지 번호 제거 (- 숫자 - 형태)
        return re.sub(r"-\s*\d+\s*-", "", text)


class BasePDFReader:
    """비동기 PDF 텍스트 추출기 기본 클래스"""

    def __init__(self, max_concurrent: int = 5):
        self.logger = logging.getLogger(__name__)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.text_cleaner = PDFTextCleaner()

    async def extract(self, pdf_path: str) -> Dict[str, Any]:
        """PDF에서 텍스트 추출 (구현 필요)"""
        raise NotImplementedError

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=True)


class PDFPypdf2Reader(BasePDFReader):
    """PyPDF2를 사용한 비동기 텍스트 추출"""

    async def extract(self, pdf_path: str) -> Dict[str, Any]:
        """PyPDF2를 사용한 비동기 텍스트 추출"""
        if not PYPDF2_AVAILABLE:
            return {"error": "PyPDF2가 설치되지 않았습니다"}

        async with self.semaphore:
            try:
                # PyPDF2는 바이너리 모드로 파일을 읽어야 함
                async with aiofiles.open(pdf_path, "rb") as file:
                    content = await file.read()

                # CPU 집약적인 PDF 파싱을 별도 스레드에서 실행
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._extract_with_pypdf2, content
                )
                return result

            except Exception as e:
                return {"method": "PyPDF2", "error": str(e)}

    def _extract_with_pypdf2(self, content: bytes) -> Dict[str, Any]:
        """PyPDF2로 실제 추출 작업 (동기 함수)"""
        import io

        try:
            text_pages = []
            metadata = {}

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            # 메타데이터 추출
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                    "producer": pdf_reader.metadata.get("/Producer", ""),
                    "creation_date": pdf_reader.metadata.get("/CreationDate", ""),
                    "modification_date": pdf_reader.metadata.get("/ModDate", ""),
                }

            # 각 페이지 텍스트 추출
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    text_pages.append(
                        {"page": page_num, "text": text, "char_count": len(text)}
                    )
                except Exception as e:
                    self.logger.error(f"PyPDF2 페이지 {page_num} 추출 오류: {e}")
                    text_pages.append({"page": page_num, "text": "", "error": str(e)})

            return {
                "method": "PyPDF2",
                "total_pages": len(text_pages),
                "metadata": metadata,
                "pages": text_pages,
                "full_text": "\n\n".join(
                    [p["text"] for p in text_pages if "text" in p]
                ),
            }

        except Exception as e:
            return {"method": "PyPDF2", "error": str(e)}


class PDFPlumberReader(BasePDFReader):
    """pdfplumber를 사용한 비동기 텍스트 추출"""

    async def extract(self, pdf_path: str) -> Dict[str, Any]:
        """pdfplumber를 사용한 비동기 텍스트 추출"""
        if not PDFPLUMBER_AVAILABLE:
            return {"error": "pdfplumber가 설치되지 않았습니다"}

        async with self.semaphore:
            try:
                # CPU 집약적인 PDF 파싱을 별도 스레드에서 실행
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._extract_with_pdfplumber, pdf_path
                )
                return result

            except Exception as e:
                return {"method": "pdfplumber", "error": str(e)}

    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """pdfplumber로 실제 추출 작업 (동기 함수)"""
        try:
            text_pages = []
            tables_data = []

            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata or {}

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # 텍스트 추출
                        text = page.extract_text()

                        # 테이블 추출
                        tables = page.extract_tables()

                        page_data = {
                            "page": page_num,
                            "text": text or "",
                            "char_count": len(text) if text else 0,
                            "tables_count": len(tables),
                            "page_width": page.width,
                            "page_height": page.height,
                        }

                        if tables:
                            page_data["tables"] = tables
                            tables_data.extend(
                                [
                                    {"page": page_num, "table_index": i, "table": table}
                                    for i, table in enumerate(tables)
                                ]
                            )

                        text_pages.append(page_data)

                    except Exception as e:
                        self.logger.error(
                            f"pdfplumber 페이지 {page_num} 추출 오류: {e}"
                        )
                        text_pages.append(
                            {"page": page_num, "text": "", "error": str(e)}
                        )

                result = {
                    "method": "pdfplumber",
                    "total_pages": len(text_pages),
                    "metadata": metadata,
                    "pages": text_pages,
                    "tables": tables_data,
                    "full_text": self.text_cleaner.clean(
                        "\n\n".join([p["text"] for p in text_pages if "text" in p])
                    ),
                }
                return result.get("full_text")

        except Exception as e:
            return {"method": "pdfplumber", "error": str(e)}


class PDFPyMuReader(BasePDFReader):
    """PyMuPDF를 사용한 비동기 텍스트 추출"""

    async def extract(self, pdf_path: str) -> Dict[str, Any]:
        """PyMuPDF를 사용한 비동기 텍스트 추출"""
        if not PYMUPDF_AVAILABLE:
            return {"error": "PyMuPDF가 설치되지 않았습니다"}
        async with self.semaphore:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._extract_with_pymupdf, pdf_path
                )
                return result

            except Exception as e:
                return {"method": "PyMuPDF", "error": str(e)}

    def _extract_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """PyMuPDF로 실제 추출 작업 (동기 함수)"""
        try:
            text_pages = []
            images_data = []

            doc = fitz.open(pdf_path)
            metadata = doc.metadata

            for page_num in range(doc.page_count):
                page = doc[page_num]

                try:
                    # 텍스트 추출
                    text = page.get_text()

                    # 이미지 정보 추출
                    images = page.get_images()

                    # 주석 정보 추출
                    annotations = []
                    for annot in page.annots():
                        annot_dict = {
                            "type": annot.type[1],
                            "content": annot.content,
                            "rect": list(annot.rect),
                        }
                        annotations.append(annot_dict)

                    page_data = {
                        "page": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                        "images_count": len(images),
                        "annotations_count": len(annotations),
                        "page_rect": list(page.rect),
                    }

                    if images:
                        page_data["images"] = [
                            {"image_index": i, "xref": img[0]}
                            for i, img in enumerate(images)
                        ]
                        images_data.extend(
                            [
                                {"page": page_num + 1, "image_index": i, "xref": img[0]}
                                for i, img in enumerate(images)
                            ]
                        )

                    if annotations:
                        page_data["annotations"] = annotations

                    text_pages.append(page_data)

                except Exception as e:
                    self.logger.error(f"PyMuPDF 페이지 {page_num + 1} 추출 오류: {e}")
                    text_pages.append(
                        {"page": page_num + 1, "text": "", "error": str(e)}
                    )

            doc.close()
            return {
                "method": "PyMuPDF",
                "total_pages": len(text_pages),
                "metadata": metadata,
                "pages": text_pages,
                "images": images_data,
                "full_text": "\n\n".join(
                    [p["text"] for p in text_pages if "text" in p]
                ),
            }

        except Exception as e:
            return {"method": "PyMuPDF", "error": str(e)}


class PDFMinerReader(BasePDFReader):
    """pdfminer를 사용한 비동기 텍스트 추출"""

    async def extract(self, pdf_path: str) -> Dict[str, Any]:
        """pdfminer를 사용한 비동기 텍스트 추출"""
        if not PDFMINER_AVAILABLE:
            return {"error": "pdfminer가 설치되지 않았습니다"}

        async with self.semaphore:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._extract_with_pdfminer, pdf_path
                )
                return result

            except Exception as e:
                return {"method": "pdfminer", "error": str(e)}

    def _extract_with_pdfminer(self, pdf_path: str) -> Dict[str, Any]:
        """pdfminer로 실제 추출 작업 (동기 함수)"""
        try:
            # 기본 텍스트 추출
            text = extract_text(
                str(pdf_path),
                laparams=LAParams(
                    boxes_flow=0.5, word_margin=0.1, char_margin=2.0, line_margin=0.5
                ),
            )

            return {
                "method": "pdfminer",
                "full_text": text,
                "char_count": len(text),
                "line_count": len(text.split("\n")),
            }

        except Exception as e:
            return {"method": "pdfminer", "error": str(e)}


class PDFMultiExtractor:
    """여러 방법으로 동시에 PDF 텍스트 추출"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)

    async def extract_all_methods(self, pdf_path: str) -> Dict[str, Any]:
        """모든 방법으로 동시에 텍스트 추출"""
        methods = []

        if PYPDF2_AVAILABLE:
            methods.append(("pypdf2", PDFPypdf2Reader))
        if PDFPLUMBER_AVAILABLE:
            methods.append(("pdfplumber", PDFPlumberReader))
        if PYMUPDF_AVAILABLE:
            methods.append(("pymupdf", PDFPyMuReader))
        if PDFMINER_AVAILABLE:
            methods.append(("pdfminer", PDFMinerReader))

        if not methods:
            return {"error": "사용 가능한 PDF 라이브러리가 없습니다"}

        # 모든 방법을 동시에 실행
        tasks = []
        for method_name, extractor_cls in methods:

            async def extract_with_method(name, cls):
                try:
                    async with cls(max_concurrent=1) as extractor:
                        return name, await extractor.extract(pdf_path)
                except Exception as e:
                    return name, {"error": str(e)}

            tasks.append(extract_with_method(method_name, extractor_cls))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 정리
        extraction_results = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                method_name, extraction_result = result
                extraction_results[method_name] = extraction_result
            elif isinstance(result, Exception):
                self.logger.error(f"추출 오류: {result}")

        return extraction_results

    async def get_best_extraction(self, pdf_path: str) -> Dict[str, Any]:
        """가장 좋은 품질의 텍스트 추출 결과 반환"""
        all_results = await self.extract_all_methods(pdf_path)

        # 오류가 없고 텍스트가 가장 많이 추출된 방법 선택
        best_method = None
        best_score = 0
        best_result = None

        for method_name, result in all_results.items():
            if "error" not in result and "full_text" in result:
                text_length = len(result["full_text"])
                if text_length > best_score:
                    best_score = text_length
                    best_method = method_name
                    best_result = result

        if best_result:
            best_result["best_method"] = best_method
            self.logger.info(
                f"{best_method} 방법이 최적으로 선택됨 (텍스트 길이: {best_score})"
            )
            return best_result
        else:
            return {
                "error": "모든 방법에서 텍스트 추출에 실패했습니다",
                "all_results": all_results,
            }

    async def extract_multiple_files(
        self, file_paths: List[str], method: str = "best", batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """여러 PDF 파일을 배치 단위로 처리"""
        results = []

        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            batch_tasks = []

            for file_path in batch:
                if method == "best":
                    task = self.get_best_extraction(file_path)
                else:
                    reader_cls = self._get_reader_class(method)
                    if reader_cls:

                        async def extract_single(path, cls):
                            async with cls(max_concurrent=1) as reader:
                                return await reader.extract(path)

                        task = extract_single(file_path, reader_cls)
                    else:
                        task = asyncio.create_task(
                            asyncio.coroutine(
                                lambda: {"error": f"지원하지 않는 방법: {method}"}
                            )()
                        )

                batch_tasks.append(task)

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append({"file_path": batch[j], "error": str(result)})
                else:
                    results.append({"file_path": batch[j], **result})

            # 배치 간 짧은 휴식
            if i + batch_size < len(file_paths):
                await asyncio.sleep(0.1)

        return results

    def _get_reader_class(self, method: str):
        """방법명에 따른 리더 클래스 반환"""
        if method == "pypdf2" and PYPDF2_AVAILABLE:
            return PDFPypdf2Reader
        elif method == "pdfplumber" and PDFPLUMBER_AVAILABLE:
            return PDFPlumberReader
        elif method == "pymupdf" and PYMUPDF_AVAILABLE:
            return PDFPyMuReader
        elif method == "pdfminer" and PDFMINER_AVAILABLE:
            return PDFMinerReader
        else:
            return None


def create_pdf_reader(
    method: str = "pdfplumber", max_concurrent: int = 5
) -> BasePDFReader:
    """비동기 PDF 리더 생성 팩토리 함수"""
    if method == "pypdf2":
        return PDFPypdf2Reader(max_concurrent)
    elif method == "pdfplumber":
        return PDFPlumberReader(max_concurrent)
    elif method == "pymupdf":
        return PDFPyMuReader(max_concurrent)
    elif method == "pdfminer":
        return PDFMinerReader(max_concurrent)
    else:
        raise ValueError(f"지원하지 않는 방법: {method}")


# ============ 편의 함수들 ============


async def extract_pdf_text_async(pdf_path: str, method: str = "best") -> Dict[str, Any]:
    """단일 PDF 파일에서 비동기 텍스트 추출"""
    if method == "best":
        extractor = PDFMultiExtractor()
        return await extractor.get_best_extraction(pdf_path)
    else:
        reader_cls = PDFMultiExtractor()._get_reader_class(method)
        if reader_cls:
            async with reader_cls(max_concurrent=1) as reader:
                return await reader.extract(pdf_path)
        else:
            return {"error": f"지원하지 않는 방법: {method}"}


async def extract_multiple_pdfs_async(
    file_paths: List[str],
    method: str = "best",
    max_concurrent: int = 5,
    batch_size: int = 10,
) -> List[Dict[str, Any]]:
    """여러 PDF 파일을 비동기로 동시 처리"""
    extractor = PDFMultiExtractor(max_concurrent)
    return await extractor.extract_multiple_files(file_paths, method, batch_size)
