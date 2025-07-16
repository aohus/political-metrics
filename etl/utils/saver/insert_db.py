import json
import logging
from typing import Any, List, Union

from pydantic import BaseModel

from model.orm import (
    Base,
    Bill,
    BillDetail,
    BillProposer,
    Committee,
    CommitteeMember,
    Member,
    MemberHistory,
)
from schema.model import Bill as PydanticBill
from schema.model import BillDetail as PydanticBillDetail
from schema.model import BillProposer as PydanticBillProposer
from schema.model import Committee as PydanticCommittee
from schema.model import CommitteeMember as PydanticCommitteeMember
from schema.model import Member as PydanticMember
from schema.model import MemberHistory as PydanticMemberHistory

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataBulkInserter:
    def __init__(self, db):
        self.db = db

    def insert_bulk_data(self, obj_list: List[Any]):
        """주어진 객체 리스트를 데이터베이스에 벌크 삽입합니다."""
        if not obj_list:
            logger.info("삽입할 데이터가 없습니다.")
            return

        model_name = obj_list[0].__class__.__name__
        logger.info(f"'{model_name}' 모델의 {len(obj_list)}개 데이터 벌크 삽입 시작...")
        try:
            self.db.bulk_save_objects(
                obj_list
            )  # ORM 객체 리스트를 삽입할 때 가장 효율적
            # 또는 self.db.add_all(obj_list) # 하나씩 add 하는 것과 같지만 리스트를 받음
            # 또는 bulk_insert_mappings()를 사용할 수도 있지만, 이건 dict 리스트를 받습니다.

            self.db.commit()
            logger.info(f"'{model_name}' 모델의 {len(obj_list)}개 데이터 삽입 완료.")
        except Exception as e:
            self.db.rollback()
            logger.error(f"'{model_name}' 모델 데이터 삽입 중 오류 발생: {e}")
            raise

    def query_data(self, model: Any, limit: int = 10) -> List[Any]:
        """주어진 모델의 데이터를 조회합니다."""
        return self.db.query(model).limit(limit).all()


info = [
    ("members", Member, PydanticMember),
    ("member_history", MemberHistory, PydanticMemberHistory),
    ("committees", Committee, PydanticCommittee),
    ("bills", Bill, PydanticBill),
    ("bill_details", BillDetail, PydanticBillDetail),
    ("bill_proposer", BillProposer, PydanticBillProposer),
    ("committee_members", CommitteeMember, PydanticCommitteeMember),
]

model_matching = {
    PydanticMember: Member,
    PydanticMemberHistory: MemberHistory,
    PydanticCommittee: Committee,
    PydanticBill: Bill,
    PydanticBillDetail: BillDetail,
    PydanticBillProposer: BillProposer,
    PydanticCommitteeMember: CommitteeMember,
}


def get_dump_data(path):
    with open(f"../data/new/{path}.json", "r") as f:
        return json.load(f)


def bulk_insert(db_session_obj, data: List[Any]):
    db_gen = DataBulkInserter(db_session_obj)

    orm_obj_list = []
    if isinstance(data[0], BaseModel):
        ORM_MODEL = model_matching.get(data[0].__class__.__name__)
        for pydantic_obj in data:
            orm_data = pydantic_obj.model_dump(exclude={"created_at"})
            orm_obj = ORM_MODEL(**orm_data)
            orm_obj_list.append(orm_obj)
    elif isinstance(data[0], Base):
        orm_obj_list = data
    else:
        for path, ORM_MODEL, PYDANTIC_MODEL in info:
            logger.info(
                f"'{ORM_MODEL.__name__}' 모델 데이터 로드 및 삽입 시작 (파일: {path})..."
            )
            data = get_dump_data(path)

            for row in data:
                try:
                    pydantic_obj = PYDANTIC_MODEL(**row)
                    orm_data = pydantic_obj.model_dump(exclude={"created_at"})
                    orm_obj = ORM_MODEL(**orm_data)
                    orm_obj_list.append(orm_obj)
                except Exception as e:
                    logger.error(
                        f"'{ORM_MODEL.__name__}' 모델 데이터 파싱/유효성 검사 실패: {row} -> {e}"
                    )
                    continue

        if orm_obj_list:
            db_gen.insert_bulk_data(orm_obj_list)
            result_count = len(db_gen.query_data(ORM_MODEL))
            logger.info(f"'{ORM_MODEL.__name__}' 총 {result_count}개 데이터 삽입 확인.")
        else:
            logger.info(f"'{ORM_MODEL.__name__}' 삽입된 데이터 없음.")
