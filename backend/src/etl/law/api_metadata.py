from typing import Dict, Optional

from utils.extract.api_schema import APISchema, BaseAPI


def law_total_counter(result: Dict, key: str) -> int:
    """법령 API 응답에서 총 개수 추출"""
    if key in result:
        total_cnt = result[key].get("totalCnt")
        return int(total_cnt) if total_cnt else 0
    return 0


class LawAPI(BaseAPI):
    """법령 API 전용 설정 및 관리 클래스"""

    BASE_URL = "http://apis.data.go.kr/1170000/law/lawSearchList.do"
    API_KEY_NAME = "LAW_API_KEY"
    AUTH_PARAM = "serviceKey"
    PAGE_SIZE_PARAM = "numOfRows"
    PAGE_NUM_PARAM = "pageNo"

    def extract_total_count(self, api_name: str, result: Dict) -> int:
        key = self.get_count_key(api_name)
        return law_total_counter(result, key)

    API_DEFINITIONS: Dict[str, APISchema] = {
        "cur_law": APISchema(
            key="law",
            count_key="LawSearch",
            endpoint="",
            default_params={
                "target": "law",
                "query": "*",
                "numOfRows": "10",
                "pageNo": "1",
            },
            valid_params={"serviceKey", "target", "query", "numOfRows", "pageNo"},
            description="현행 법령 목록 조회",
        ),
        "cur_admrul": APISchema(
            key="admrul",
            count_key="AdmRulSearch",
            endpoint="",
            default_params={
                "target": "admrul",
                "query": "*",
                "numOfRows": "10",
                "pageNo": "1",
            },
            valid_params={"serviceKey", "target", "query", "numOfRows", "pageNo"},
            description="행정 규칙 목록 조회",
        ),
        "cur_ordin": APISchema(
            key="law",
            count_key="OrdinSearch",
            endpoint="",
            default_params={
                "target": "ordin",
                "query": "*",
                "numOfRows": "10",
                "pageNo": "1",
            },
            valid_params={"serviceKey", "target", "query", "numOfRows", "pageNo"},
            description="자치 법령 목록 조회",
        ),
        "cur_trty": APISchema(
            key="Trty",
            count_key="TrtySearch",
            endpoint="",
            default_params={
                "target": "trty",
                "query": "*",
                "numOfRows": "10",
                "pageNo": "1",
            },
            valid_params={"serviceKey", "target", "query", "numOfRows", "pageNo"},
            description="조약 정보 목록 조회",
        ),
    }
