import inspect
import json
import sqlite3
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator


class PydanticDBGenerator:
    """Pydantic 모델을 기반으로 DB 테이블 생성 및 데이터 삽입을 처리하는 클래스"""

    def __init__(self, db_path: str = "assembly_data.db"):
        self.db_path = db_path
        self.conn = None

        # 타입 매핑 테이블
        self.type_mapping = {
            str: "TEXT",
            int: "INTEGER",
            float: "REAL",
            bool: "BOOLEAN",
            datetime: "TEXT",  # ISO format으로 저장
            "Optional": "TEXT",
            "default": "TEXT",
        }

        # 기본키 및 외래키 정의
        self.primary_keys = {
            "RawMemberData": "NAAS_CD",
            "Bill": "BILL_ID",
            "BillDetail": "BILL_ID",
            "Committee": "COMMITTEE_ID",
            "BillProposer": None,  # 복합키
            "CommitteeMember": None,  # 복합키
        }

        self.foreign_keys = {
            "BillDetail": [("BILL_ID", "Bill", "BILL_ID")],
            "BillProposer": [
                ("BILL_ID", "Bill", "BILL_ID"),
                ("POLITICIAN_ID", "RawMemberData", "NAAS_CD"),
            ],
            "CommitteeMember": [
                ("COMMITTEE_ID", "Committee", "COMMITTEE_ID"),
                ("MEMBER_ID", "RawMemberData", "NAAS_CD"),
            ],
        }

    def connect(self):
        """데이터베이스 연결"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # 외래키 제약조건 활성화
        return self.conn

    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()

    def get_sql_type(self, field_info) -> str:
        """Pydantic 필드 정보를 SQL 타입으로 변환"""
        field_type = field_info.type_

        # Optional 타입 처리
        if hasattr(field_type, "__origin__"):
            if field_type.__origin__ is Union:
                # Optional[Type]은 Union[Type, None]과 같음
                non_none_types = [t for t in field_type.__args__ if t is not type(None)]
                if non_none_types:
                    field_type = non_none_types[0]

        # Enum 타입 처리
        if hasattr(field_type, "__bases__") and any(
            base.__name__ == "Enum" for base in field_type.__bases__
        ):
            return "TEXT"

        return self.type_mapping.get(field_type, self.type_mapping["default"])

    def generate_create_table_sql(self, model_class) -> str:
        """Pydantic 모델로부터 CREATE TABLE SQL 구문 생성"""
        table_name = model_class.__name__
        field_definitions = []

        # 필드 정의 생성
        for field_name, field_info in model_class.__fields__.items():
            sql_type = self.get_sql_type(field_info)
            definition = f"{field_name} {sql_type}"

            # 기본키 설정
            if self.primary_keys.get(table_name) == field_name:
                definition += " PRIMARY KEY"

            # Field의 max_length 제약조건 처리
            if hasattr(field_info, "field_info") and hasattr(
                field_info.field_info, "max_length"
            ):
                max_length = field_info.field_info.max_length
                if max_length and sql_type == "TEXT":
                    definition = definition.replace("TEXT", f"VARCHAR({max_length})")

            field_definitions.append(definition)

        # 외래키 제약조건 추가
        if table_name in self.foreign_keys:
            for fk_field, ref_table, ref_field in self.foreign_keys[table_name]:
                fk_constraint = (
                    f"FOREIGN KEY ({fk_field}) REFERENCES {ref_table}({ref_field})"
                )
                field_definitions.append(fk_constraint)

        # 복합키 처리
        if table_name == "BillProposer":
            field_definitions.append("PRIMARY KEY (BILL_ID, POLITICIAN_ID)")
        elif table_name == "CommitteeMember":
            field_definitions.append("PRIMARY KEY (COMMITTEE_ID, MEMBER_ID)")

        sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
    {',\n    '.join(field_definitions)}
);"""
        return sql

    def generate_insert_sql(self, model_instance: BaseModel) -> tuple:
        """Pydantic 모델 인스턴스로부터 INSERT SQL 구문과 값들 생성"""
        table_name = type(model_instance).__name__

        # Pydantic의 dict() 메서드 사용 (JSON 호환 형태로 변환)
        data_dict = model_instance.dict()

        # datetime 객체를 문자열로 변환
        for key, value in data_dict.items():
            if isinstance(value, datetime):
                data_dict[key] = value.isoformat()

        fields_list = list(data_dict.keys())
        values_list = list(data_dict.values())
        placeholders = ", ".join(["?" for _ in fields_list])

        sql = f"""INSERT OR REPLACE INTO {table_name} 
({', '.join(fields_list)}) 
VALUES ({placeholders})"""

        return sql, values_list

    def create_all_tables(self):
        """모든 테이블 생성"""
        if not self.conn:
            self.connect()

        # 테이블 생성 순서 (외래키 관계 고려)
        model_classes = [
            RawMemberData,
            Committee,
            Bill,
            BillDetail,
            BillProposer,
            CommitteeMember,
        ]

        for model_class in model_classes:
            sql = self.generate_create_table_sql(model_class)
            print(f"Creating table {model_class.__name__}...")
            print(sql)
            print("-" * 50)
            self.conn.execute(sql)

        self.conn.commit()
        print("All tables created successfully!")

    def insert_data(self, model_instance: BaseModel):
        """단일 데이터 삽입 (Pydantic 검증 포함)"""
        if not self.conn:
            self.connect()

        try:
            # Pydantic이 자동으로 검증 수행
            sql, values = self.generate_insert_sql(model_instance)
            self.conn.execute(sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting data: {e}")
            return False

    def insert_bulk_data(self, model_instances: List[BaseModel]):
        """대량 데이터 삽입 (Pydantic 검증 포함)"""
        if not self.conn:
            self.connect()

        if not model_instances:
            return

        try:
            # 모든 인스턴스 검증 및 SQL 생성
            sql, _ = self.generate_insert_sql(model_instances[0])

            values_list = []
            for instance in model_instances:
                # 각 인스턴스마다 Pydantic 검증 수행
                _, values = self.generate_insert_sql(instance)
                values_list.append(values)

            self.conn.executemany(sql, values_list)
            self.conn.commit()
            print(f"Successfully inserted {len(values_list)} records")
            return True
        except Exception as e:
            print(f"Error in bulk insert: {e}")
            return False

    def insert_from_json(self, json_data: Union[str, dict, List[dict]], model_class):
        """JSON 데이터를 Pydantic 모델로 변환하여 삽입"""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data

            if isinstance(data, list):
                # 리스트인 경우 대량 삽입
                instances = [model_class(**item) for item in data]
                return self.insert_bulk_data(instances)
            else:
                # 단일 객체인 경우
                instance = model_class(**data)
                return self.insert_data(instance)

        except Exception as e:
            print(f"Error processing JSON data: {e}")
            return False

    def query_data(
        self, table_name: str, condition: str = "", limit: int = None
    ) -> List[dict]:
        """데이터 조회"""
        if not self.conn:
            self.connect()

        sql = f"SELECT * FROM {table_name}"
        if condition:
            sql += f" WHERE {condition}"
        if limit:
            sql += f" LIMIT {limit}"

        cursor = self.conn.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def query_to_pydantic(
        self, model_class, condition: str = "", limit: int = None
    ) -> List[BaseModel]:
        """데이터 조회 후 Pydantic 모델로 변환"""
        table_name = model_class.__name__
        data = self.query_data(table_name, condition, limit)

        try:
            return [model_class(**row) for row in data]
        except Exception as e:
            print(f"Error converting to Pydantic models: {e}")
            return []


def main():
    """사용 예시"""
    # DB 생성기 초기화
    db_gen = PydanticDBGenerator("assembly_data.db")

    try:
        # 모든 테이블 생성
        db_gen.create_all_tables()

        # 샘플 데이터 생성 및 삽입 (Pydantic 검증 포함)
        print("\n=== 샘플 데이터 삽입 (Pydantic 검증) ===")

        # 의원 데이터 (검증 포함)
        member1 = RawMemberData(
            NAAS_CD="MP001",
            NAAS_NM="김의원",
            PLPT_NM="더불어민주당",
            ELECD_NM="서울 강남구 갑",
            NAAS_EMAIL_ADDR="kim@assembly.go.kr",  # 이메일 검증
            NAAS_HP_URL="https://kim.assembly.go.kr",  # URL 검증
            NTR_DIV=Gender.MALE,
        )

        # 위원회 데이터
        committee1 = Committee(
            COMMITTEE_ID=1, COMMITTEE_NAME="법제사법위원회", COMMITTEE_TYPE="상임위원회"
        )

        # 의안 데이터 (Enum 사용)
        bill1 = Bill(
            BILL_ID="BILL001",
            BILL_NO="2210001",
            BILL_NAME="테스트 법률안",
            COMMITTEE_ID=1,
            STATUS=BillStatus.IN_PROGRESS,  # Enum 값
        )

        # 의안 상세 데이터
        bill_detail1 = BillDetail(
            BILL_ID="BILL001",
            RST_PROPOSER="김의원",
            PROC_RESULT="심사중",
            DETAIL_LINK="https://likms.assembly.go.kr/bill/detail",
        )

        # 발의자 관계 데이터
        proposer1 = BillProposer(BILL_ID="BILL001", POLITICIAN_ID="MP001", RST=True)

        # 위원회 구성원 데이터
        committee_member1 = CommitteeMember(
            COMMITTEE_ID=1,
            MEMBER_ID="MP001",
            MEMBER_NAME="김의원",
            MEMBER_TYPE="위원장",
        )

        # 데이터 삽입 (자동 검증)
        sample_data = [
            member1,
            committee1,
            bill1,
            bill_detail1,
            proposer1,
            committee_member1,
        ]

        for data in sample_data:
            success = db_gen.insert_data(data)
            print(f"Insert {type(data).__name__}: {'Success' if success else 'Failed'}")

        # JSON 데이터 삽입 예시
        print("\n=== JSON 데이터 삽입 ===")
        json_member_data = {
            "NAAS_CD": "MP002",
            "NAAS_NM": "이의원",
            "PLPT_NM": "국민의힘",
            "NAAS_EMAIL_ADDR": "lee@assembly.go.kr",
            "NTR_DIV": "여",
        }

        success = db_gen.insert_from_json(json_member_data, RawMemberData)
        print(f"JSON Insert: {'Success' if success else 'Failed'}")

        # Pydantic 모델로 조회
        print("\n=== Pydantic 모델로 데이터 조회 ===")
        members = db_gen.query_to_pydantic(RawMemberData, limit=5)
        for member in members:
            print(f"의원: {member.NAAS_NM} ({member.PLPT_NM}) - {member.NTR_DIV}")
            # Pydantic 모델이므로 검증된 데이터
            print(f"  이메일 검증됨: {member.NAAS_EMAIL_ADDR}")

        # 일반 딕셔너리로 조회
        bills = db_gen.query_data("Bill", "STATUS = '진행중'")
        for bill in bills:
            print(f"의안: {bill['BILL_NAME']} - {bill['STATUS']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db_gen.close()


def validation_example():
    """Pydantic 검증 기능 예시"""
    print("\n=== Pydantic 검증 예시 ===")

    try:
        # 올바른 데이터
        valid_member = RawMemberData(
            NAAS_CD="MP003",
            NAAS_NM="박의원",
            NAAS_EMAIL_ADDR="park@assembly.go.kr",
            NAAS_HP_URL="https://park.assembly.go.kr",
        )
        print(f"유효한 데이터: {valid_member.NAAS_NM}")

    except Exception as e:
        print(f"검증 실패: {e}")

    try:
        # 잘못된 이메일
        invalid_member = RawMemberData(
            NAAS_CD="MP004", NAAS_NM="최의원", NAAS_EMAIL_ADDR="invalid-email"  # @ 없음
        )

    except Exception as e:
        print(f"이메일 검증 실패: {e}")

    try:
        # 잘못된 URL
        invalid_member2 = RawMemberData(
            NAAS_CD="MP005", NAAS_NM="정의원", NAAS_HP_URL="invalid-url"  # http:// 없음
        )

    except Exception as e:
        print(f"URL 검증 실패: {e}")


def json_integration_example():
    """JSON 통합 예시"""
    print("\n=== JSON 통합 예시 ===")

    db_gen = PydanticDBGenerator("assembly_data.db")

    try:
        # JSON 문자열로부터 데이터 생성
        json_str = """
        [
            {
                "NAAS_CD": "MP010",
                "NAAS_NM": "김JSON",
                "PLPT_NM": "더불어민주당",
                "NAAS_EMAIL_ADDR": "json@assembly.go.kr",
                "NTR_DIV": "남"
            },
            {
                "NAAS_CD": "MP011", 
                "NAAS_NM": "이JSON",
                "PLPT_NM": "국민의힘",
                "NAAS_EMAIL_ADDR": "json2@assembly.go.kr",
                "NTR_DIV": "여"
            }
        ]
        """

        db_gen.create_all_tables()
        success = db_gen.insert_from_json(json_str, RawMemberData)
        print(f"JSON 대량 삽입: {'Success' if success else 'Failed'}")

        # 결과 확인
        members = db_gen.query_to_pydantic(RawMemberData, "NAAS_NM LIKE '%JSON%'")
        for member in members:
            print(f"JSON 삽입된 의원: {member.NAAS_NM} ({member.NTR_DIV})")
            # Pydantic 모델의 JSON 출력
            print(f"  JSON: {member.json()}")

    finally:
        db_gen.close()


if __name__ == "__main__":
    # 기본 예시 실행
    main()

    # 검증 예시 (주석 해제하여 실행)
    validation_example()

    # JSON 통합 예시 (주석 해제하여 실행)
    json_integration_example()
