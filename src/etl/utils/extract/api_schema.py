import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
from urllib.parse import urlencode

from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


@dataclass(frozen=True)
class APISchema:
    """API 엔드포인트의 스키마와 설정을 나타냄"""

    endpoint: str  # 실제 엔드포인트 (base_url 제외)
    key: str
    count_key: str = None
    req_params: Dict[str, Any] = field(default_factory=dict)
    default_params: Dict[str, Any] = field(default_factory=dict)
    valid_params: Set[str] = field(default_factory=set)
    description: str = ""


class BaseAPI(ABC):
    """API 공통 인터페이스"""

    BASE_URL: str
    API_KEY_NAME: str
    AUTH_PARAM: str
    PAGE_SIZE_PARAM: str
    PAGE_NUM_PARAM: str

    def __init__(self):
        self.api_key = self.get_api_key()
        if not self.api_key:
            logger.warning(f"{self.API_KEY_NAME} not found in environment variables")

    @property
    def BASE_URL(self) -> str:
        return self.BASE_URL

    @property
    def AUTH_PARAM(self) -> str:
        return self.AUTH_PARAM

    @property
    def PAGE_SIZE_PARAM(self) -> str:
        return self.PAGE_SIZE_PARAM

    @property
    def PAGE_NUM_PARAM(self) -> str:
        return self.PAGE_NUM_PARAM

    @property
    def API_DEFINITIONS(self) -> Dict[str, APISchema]:
        return self.API_DEFINITIONS

    def get_api_key(self) -> Optional[str]:
        """API 키 반환"""
        return os.getenv(self.API_KEY_NAME)

    def get_key(self, api_name: str) -> Optional[str]:
        schema = self.get_schema(api_name)
        if not schema:
            raise ValueError(f"Unknown API: {api_name}")
        return schema.key

    def get_count_key(self, api_name: str) -> Optional[str]:
        schema = self.get_schema(api_name)
        if not schema:
            raise ValueError(f"Unknown API: {api_name}")
        return schema.count_key

    def get_schema(self, api_name: str) -> Optional[APISchema]:
        """API 스키마 반환"""
        return self.API_DEFINITIONS.get(api_name)

    def get_endpoint(self, api_name: str) -> str:
        """API 엔드포인트 반환"""
        schema = self.get_schema(api_name)
        if not schema:
            raise ValueError(f"Unknown API: {api_name}")
        return schema.endpoint

    def validate_params(self, api_name: str, **kwargs) -> Dict[str, Any]:
        """파라미터 검증 및 기본값 설정"""
        if api_name not in self.API_DEFINITIONS:
            raise ValueError(f"Unknown API name: {api_name}")

        schema = self.get_schema(api_name)

        path_params, req_params = {}, {}
        for key, value in schema.default_params.items():
            if key not in kwargs.keys():
                path_params[key] = value

        for key, value in schema.req_params.items():
            if key not in kwargs.keys():
                req_params[key] = value

        for key, value in kwargs.items():
            if key in schema.valid_params.keys():
                path_params[key] = value
            elif key in schema.req_args.keys():
                req_params[key] = value
            else:
                logger.warning(
                    f"Invalid parameter '{key}:{value}' for API '{api_name}'"
                )

        # API 키 추가
        if self.api_key:
            if self.AUTH_PARAM in schema.req_params.keys():
                req_params[self.AUTH_PARAM] = self.api_key
            else:
                path_params[self.AUTH_PARAM] = self.api_key

        return (path_params, req_params)

    def build_url(self, api_name: str, **params) -> str:
        """URL 생성"""
        validated_params, req_params = self.validate_params(api_name, **params)
        endpoint = self.get_endpoint(api_name)
        full_url = f"{self.BASE_URL}{endpoint}"

        if validated_params:
            return f"{full_url}?{urlencode(validated_params)}"
        return full_url, req_params

    @abstractmethod
    def extract_total_count(self, api_name: str, result: Dict) -> int:
        """응답에서 총 개수 추출 - 각 API별로 구현"""
        pass
