import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import pandas as pd
import xmltodict
from dotenv import load_dotenv
from tqdm import tqdm

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class ResponseParser:
    """응답 형식 감지 및 파싱 클래스"""

    @staticmethod
    def detect_format(text: str, content_type: str = None) -> str:
        """응답 형식 감지 (json, xml, text)"""
        text_stripped = text.strip()

        # Content-Type 헤더로 먼저 판단
        if content_type:
            if "json" in content_type.lower():
                return "json"
            elif "xml" in content_type.lower():
                return "xml"

        # 내용으로 판단
        if text_stripped.startswith(("<?xml", "<")):
            return "xml"
        elif text_stripped.startswith(("{", "[")):
            return "json"
        else:
            return "text"

    @staticmethod
    def parse_response(text: str, content_type: str = None) -> Optional[Dict]:
        """응답을 적절한 형식으로 파싱"""
        format_type = ResponseParser.detect_format(text, content_type)

        if format_type == "json":
            try:
                result = json.loads(text)
                logger.debug("JSON 형식으로 파싱 성공")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패, XML 시도: {e}")
                # JSON 파싱 실패 시 XML 시도
                format_type = "xml"

        if format_type == "xml":
            try:
                result = xmltodict.parse(text)
                logger.debug("XML 형식으로 파싱 성공")
                return result
            except Exception as e:
                logger.warning(f"XML 파싱 실패, JSON 시도: {e}")
                # XML 파싱 실패 시 JSON 시도
                try:
                    result = json.loads(text)
                    logger.debug("JSON 형식으로 재파싱 성공")
                    return result
                except json.JSONDecodeError:
                    logger.error("JSON, XML 모든 파싱 방법 실패")
                    return None

        # 둘 다 아닌 경우 텍스트로 반환
        logger.warning(f"알 수 없는 응답 형식: {format_type}")
        return {"raw_text": text}


class HTTPClient:
    """HTTP 요청 전용 클래스"""

    def __init__(
            self, 
            max_concurrent_requests: int = 10, 
            retry_attempts: int = 3, 
            delay_between_requests: float = 0.5
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.retry_attempts = retry_attempts
        self.delay_between_requests = delay_between_requests
        self.session = None
        self.parser = ResponseParser()
        self._is_session_owner = False

    async def __aenter__(self):
        if self.session is None:
            await self.create_session()
            self._is_session_owner = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._is_session_owner:
            await self.close_session()

    async def create_session(self):
        """세션 생성"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                ssl=False,
                limit=100,
                limit_per_host=30,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
            )
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
            logger.info("HTTP 세션 생성됨")

    async def close_session(self):
        """세션 종료"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("HTTP 세션 종료됨")
        self.session = None
        self._is_session_owner = False

    async def ensure_session(self):
        """세션이 없으면 생성"""
        if self.session is None or self.session.closed:
            await self.create_session()

    async def make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """API 요청 실행 (비동기)"""
        await self.ensure_session()  # 세션 확인

        async with self.semaphore:
            max_retries = self.retry_attempts
            retry_delay = self.delay_between_requests

            for attempt in range(max_retries):
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json, application/xml, text/plain, */*",
                        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                    }

                    async with self.session.get(url, params=params, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            text = await response.text(encoding="utf-8")
                            content_type = response.headers.get("Content-Type", "")

                            # 응답 형식 로깅
                            format_detected = ResponseParser.detect_format(text, content_type)
                            logger.debug(f"응답 형식: {format_detected}, Content-Type: {content_type}")

                            # 응답 파싱
                            result = self.parser.parse_response(text, content_type)
                            if result is None:
                                logger.error(f"파싱 실패. 응답 내용 일부: {text[:200]}...")
                            return result
                        else:
                            logger.warning(f"HTTP 오류: {response.status} - {response.reason}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2
                                continue
                            return None
                except Exception as e:
                    logger.error(f"요청 오류 (시도 {attempt + 1}): {e}", exc_info=True)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    return None
            return None
