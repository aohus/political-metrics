import logging
from datetime import datetime
from typing import List, Optional

from core.schema.utils import BillStatus, Gender
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


Base = declarative_base()


# ============ SQLAlchemy ORM 모델들 ============
class MemberHistory(Base):
    """국회의원 이력 정보 테이블"""

    __tablename__ = "member_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    AGE = Column(String(10), nullable=False, comment="당선대수")
    NAAS_NM = Column(String(10), nullable=False, comment="국회의원명")
    MEMBER_ID = Column(
        String(50),
        ForeignKey("members.MEMBER_ID"),
        nullable=False,
        index=True,
        comment="국회의원코드",
    )
    DTY_NM = Column(String(100), nullable=True, comment="직책명")
    ELECD_NM = Column(String(100), nullable=True, comment="선거구명")
    ELECD_DIV_NM = Column(String(50), nullable=True, comment="선거구구분명")
    PLPT_NM = Column(String(100), nullable=True, comment="정당명")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")

    # MEMBER_ID는 Member 테이블의 MEMBER_ID를 참조하는 FK
    member = relationship("Member", back_populates="histories")

    def __repr__(self):
        return f"<MemberHistory(id={self.id}, MEMBER_ID='{self.MEMBER_ID}', AGE='{self.AGE}')>"


class Member(Base):
    """국회의원 정보 테이블"""

    __tablename__ = "members"

    MEMBER_ID = Column(
        String(50), primary_key=True, index=True, comment="국회의원코드"
    )  # 필수 필드
    NAAS_NM = Column(String(100), nullable=False, comment="국회의원명")  # 필수 필드
    BIRDY_DT = Column(String(20), nullable=True, comment="생일일자")
    DTY_NM = Column(String(100), nullable=True, comment="직책명")
    PLPT_NM = Column(String(100), nullable=True, comment="정당명")
    ELECD_NM = Column(String(100), nullable=True, comment="선거구명")
    ELECD_DIV_NM = Column(String(50), nullable=True, comment="선거구구분명")
    CMIT_NM = Column(String(200), nullable=True, comment="위원회명")
    BLNG_CMIT_NM = Column(String, nullable=True, comment="소속위원회명")
    RLCT_DIV_NM = Column(String(50), nullable=True, comment="재선구분명")
    GTELT_ERACO = Column(String(50), nullable=True, comment="당선대수")
    NTR_DIV = Column(SQLEnum(Gender, name="gender_enum"), nullable=True, comment="성별")
    NAAS_HP_URL = Column(String(500), nullable=True, comment="국회의원홈페이지URL")
    BRF_HST = Column(String, nullable=True, comment="약력")
    NAAS_PIC = Column(String(500), nullable=True, comment="국회의원 사진")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")

    # 관계 정의
    histories = relationship("MemberHistory", back_populates="member")
    proposed_bills = relationship("BillProposer", back_populates="proposer")
    committee_memberships = relationship("CommitteeMember", back_populates="member")
    member_bill_stats = relationship("MemberBillStatistic", back_populates="member")

    def __repr__(self):
        return f"<Member(MEMBER_ID='{self.MEMBER_ID}', NAAS_NM='{self.NAAS_NM}')>"


class Bill(Base):
    """의안 정보 테이블"""

    __tablename__ = "bills"

    BILL_ID = Column(String(100), primary_key=True, index=True, comment="의안ID")
    BILL_NO = Column(String(50), nullable=False, unique=True, comment="의안번호")
    AGE = Column(String(10), nullable=True, comment="대수")
    BILL_NAME = Column(String(500), nullable=False, comment="법률안명")  # 필수 필드
    COMMITTEE_NAME = Column(
        String(200),
        ForeignKey("committees.COMMITTEE_NAME"),
        nullable=True,
        comment="소관위원회",
    )
    PROPOSE_DT = Column(DateTime, nullable=True, comment="제안일")
    PROC_DT = Column(DateTime, nullable=True, comment="의결일")
    STATUS = Column(
        SQLEnum(BillStatus, name="bill_status_enum"),
        nullable=False,
        default=BillStatus.COMMITTEE_PENDING,
        comment="의안상태",
    )

    # 관계 정의
    committee = relationship("Committee", back_populates="bills")
    detail = relationship("BillDetail", back_populates="bill", uselist=False)
    proposers = relationship("BillProposer", back_populates="bill")

    def __repr__(self):
        return f"<Bill(BILL_ID='{self.BILL_ID}', BILL_NAME='{self.BILL_NAME}')>"


class BillDetail(Base):
    """의안 상세 정보 테이블"""

    __tablename__ = "bill_details"

    BILL_ID = Column(
        String(100), ForeignKey("bills.BILL_ID"), primary_key=True, comment="의안ID"
    )
    PROC_DT = Column(DateTime, nullable=True, comment="의결일")
    DETAIL_LINK = Column(String(1000), nullable=True, comment="상세페이지")
    LAW_SUBMIT_DT = Column(DateTime, nullable=True, comment="법사위회부일")
    LAW_PRESENT_DT = Column(DateTime, nullable=True, comment="법사위상정일")
    LAW_PROC_DT = Column(DateTime, nullable=True, comment="법사위처리일")
    LAW_PROC_RESULT_CD = Column(String(50), nullable=True, comment="법사위처리결과")
    COMMITTEE_DT = Column(String(20), nullable=True, comment="소관위회부일")
    CMT_PRESENT_DT = Column(DateTime, nullable=True, comment="소관위상정일")
    CMT_PROC_DT = Column(DateTime, nullable=True, comment="소관위처리일")
    CMT_PROC_RESULT_CD = Column(String(50), nullable=True, comment="소관위처리결과")
    PROC_RESULT = Column(String(100), nullable=True, comment="본회의심의결과")

    # 관계 정의
    bill = relationship("Bill", back_populates="detail")

    def __repr__(self):
        return f"<BillDetail(BILL_ID='{self.BILL_ID}')>"


class BillProposer(Base):
    """의안 발의자 관계 테이블 (다대다 관계를 위한 조인 테이블)"""

    __tablename__ = "bill_proposers"

    BILL_ID = Column(
        String(100), ForeignKey("bills.BILL_ID"), primary_key=True, comment="의안ID"
    )
    MEMBER_ID = Column(
        String(50),
        ForeignKey("members.MEMBER_ID"),
        primary_key=True,
        comment="정치인ID",
    )
    RST = Column(Boolean, default=False, comment="대표발의자 여부")

    # 관계 정의
    bill = relationship("Bill", back_populates="proposers")
    proposer = relationship("Member", back_populates="proposed_bills")

    def __repr__(self):
        return (
            f"<BillProposer(BILL_ID='{self.BILL_ID}', MEMBER_ID='{self.MEMBER_ID}', "
            f"RST={self.RST})>"
        )


class Committee(Base):
    """위원회 정보 테이블"""

    __tablename__ = "committees"

    COMMITTEE_ID = Column(String(20), nullable=True, comment="위원회ID")
    COMMITTEE_NAME = Column(
        String(100), nullable=False, primary_key=True, comment="위원회명"
    )
    COMMITTEE_TYPE = Column(
        String(50), nullable=False, default="", comment="위원회유형"
    )
    COMMITTEE_TYPE_CODE = Column(
        String(20), nullable=False, default="", comment="위원회유형코드"
    )
    LIMIT_CNT = Column(Integer, nullable=True, comment="위원정수")  # 필수 필드
    CURR_CNT = Column(Integer, nullable=True, comment="현원")  # 필수 필드
    POLY99_CNT = Column(Integer, nullable=True, comment="비교섭단체위원수")  # 필수 필드
    POLY_CNT = Column(Integer, nullable=True, comment="교섭단체위원수")  # 필수 필드
    ORDER_NUM = Column(String(20), nullable=True, comment="순서")

    # 관계 정의
    bills = relationship("Bill", back_populates="committee")
    memberships = relationship("CommitteeMember", back_populates="committee")

    def __repr__(self):
        return (
            f"<Committee(COMMITTEE_ID='{self.COMMITTEE_ID}', "
            f"COMMITTEE_NAME='{self.COMMITTEE_NAME}')>"
        )


class CommitteeMember(Base):
    """위원회 구성원 테이블"""

    __tablename__ = "committee_members"
    COMMITTEE_NAME = Column(
        String(200),
        ForeignKey("committees.COMMITTEE_NAME"),
        primary_key=True,
        comment="위원회ID",
    )
    MEMBER_ID = Column(
        String(50), ForeignKey("members.MEMBER_ID"), primary_key=True, comment="의원ID"
    )  # 필수 필드
    MEMBER_TYPE = Column(String(50), nullable=True, comment="의원유형")

    # 관계 정의
    committee = relationship("Committee", back_populates="memberships")
    member = relationship("Member", back_populates="committee_memberships")

    def __repr__(self):
        return (
            f"<CommitteeMember(COMMITTEE_NAME='{self.COMMITTEE_NAME}', "
            f"MEMBER_ID='{self.MEMBER_ID}', MEMBER_TYPE='{self.MEMBER_TYPE}')>"
        )


class MemberBillStatistic(Base):
    """국회의원 의안관련 통계 테이블"""

    __tablename__ = "member_bill_statistics"
    MEMBER_ID = Column(
        String(50), ForeignKey("members.MEMBER_ID"), primary_key=True, comment="의원ID"
    )  # 필수 필드
    total_count = Column(Integer, nullable=False, comment="총 발의 의안 수")
    total_pass_rate = Column(Float, nullable=False, comment="의안 통과율")
    lead_count = Column(Integer, nullable=False, comment="대표 발의 의안 수")
    lead_pass_rate = Column(Float, nullable=False, comment="대표 발의 의안 통과율")
    co_count = Column(Integer, nullable=False, comment="공동 발의 의안 수")
    co_pass_rate = Column(Float, nullable=False, comment="공동 발의 의안 통과율")
    updated_at = Column(DateTime, default=datetime.now, comment="최종 수정 일시")

    # 관계 정의
    member = relationship("Member", back_populates="member_bill_stats")

    def __repr__(self):
        return (
            f"<MemberBillStatistic(MEMBER_ID='{self.MEMBER_ID}'"
            f"total_count={self.total_count})>"
        )
