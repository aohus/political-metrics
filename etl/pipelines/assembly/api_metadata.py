from datetime import datetime, timedelta
from typing import Dict, Optional

from utils.api.api_schema import APISchema, BaseAPI


def assembly_total_counter(result: Dict, key: str) -> int:
    """국회 API 응답에서 총 개수 추출"""
    if key in result and len(result[key]) > 0 and "head" in result[key][0]:
        return int(result[key][0]["head"][0]["list_total_count"])
    return 0


class AssemblyAPI(BaseAPI):
    """국회 API 전용 설정 및 관리 클래스"""

    BASE_URL = "https://open.assembly.go.kr/portal/openapi/"
    API_KEY_NAME = "ASSEMBLY_API_KEY"
    AUTH_PARAM = "KEY"
    PAGE_SIZE_PARAM = "pSize"
    PAGE_NUM_PARAM = "pIndex"

    def extract_total_count(self, api_name: str, result: dict) -> int:
        key = self.get_key(api_name)
        return assembly_total_counter(result, key)

    def extract_rows(self, api_name: str, data: list) -> list:
        row_data = []
        for page in data:
            row_data.extend(page[self.get_endpoint(api_name)][1]["row"])
        return row_data

    # 국회 API 정의
    API_DEFINITIONS: Dict[str, APISchema] = {
        "law_bill_member": APISchema(
            endpoint="nzmimeepazxkubdpn",
            key="nzmimeepazxkubdpn",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 1,
                "KEY": None,
            },
            default_params={
                "AGE": "22",
            },
            valid_params={
                "BILL_ID",
                "BILL_NO",
                "BILL_NAME",
                "COMMITTEE",
                "PROC_RESULT",
                "PROPOSER",
                "COMMITTEE_ID",
                "AGE",
            },
            description="국회의원 법률안 정보 조회",
        ),
        "law_bill_cap": APISchema(
            endpoint="TVBPMBILL11",
            key="TVBPMBILL11",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 1,
                "KEY": None,
            },
            default_params={
                "AGE": "22",
                "PROPOSER_KIND": "위원장",
            },
            valid_params={
                "BILL_ID",
                "BILL_NO",
                "BILL_NAME",
                "PROPOSER",
                "PROPOSER_KIND",
                "CURR_COMMITTEE_ID",
                "CURR_COMMITTEE",
                "PROC_RESULT_CD",
                "PROC_DT",
                "AGE",
            },
            description="전체 법률안 정보 조회(위원장 발의)",
        ),
        "law_bill_gov": APISchema(
            endpoint="TVBPMBILL11",
            key="TVBPMBILL11",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 1,
                "KEY": None,
            },
            default_params={
                "AGE": "22",
                "PROPOSER_KIND": "정부",
            },
            valid_params={
                "BILL_ID",
                "BILL_NO",
                "BILL_NAME",
                "PROPOSER",
                "CURR_COMMITTEE_ID",
                "CURR_COMMITTEE",
                "PROC_RESULT_CD",
                "PROC_DT",
                "AGE",
            },
            description="전체 법률안 정보 조회(정부 발의)",
        ),
        "all_bill": APISchema(
            endpoint="ALLBILL",
            key="ALLBILL",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 1,
                "KEY": None,
            },
            default_params={
                "BILL_NO": None,
            },
            valid_params=set(),
            description="전체 법안 정보",
        ),
        "all_member": APISchema(
            endpoint="ALLMEMBER",
            key="ALLMEMBER",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 1,
                "KEY": None,
            },
            default_params={},
            valid_params={"NAAS_CD", "NAAS_NAME", "BLNG_CMIT_NM", "PLPT_NM"},
            description="전체 국회의원 정보 조회",
        ),
        "taking": APISchema( 
            endpoint="npbzvuwvasdqldskm",
            key="npbzvuwvasdqldskm",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 10,
                "KEY": None,
            },
            default_params={"TAKING_DATE": str((datetime.now() - timedelta(days=1)).date())},
            valid_params={"TITLE", "PERSON"},
            description="국회의원 활동 정보 조회",
        ),
        "activity": APISchema(
            endpoint="NAMEMBEREVENT",
            key="NAMEMBEREVENT",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 10,
                "KEY": None,
            },
            default_params={"NAAS_CD": "TEST"},
            valid_params={},
            description="국회의원 활동 정보 조회",
        ),
        "cur_member": APISchema(
            endpoint="nwvrqwxyaytdsfvhu",
            key="nwvrqwxyaytdsfvhu",
            req_params={
                "Type": "json",
                "pIndex": 1,
                "pSize": 10,
                "KEY": None,
            },
            default_params={},
            valid_params={
                "HG_NM",
                "POLY_NM",
                "ORIG_NM",
                "CMITS",
                "SEX_GBN_NM",
                "MONA_CD",
            },
            description="현역 국회의원 정보 조회",
        ),
    }
