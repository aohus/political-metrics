from dataclasses import dataclass, fields
from enum import Enum
from typing import Optional

from .mixins import model_meta


class BaseDataObject(metaclass=model_meta):
    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.goal}"

    def __repr__(self) -> str:
        return self.__str__()

    def to_tuple(self) -> tuple:
        return tuple(self.get_field_values())

    @property
    def to_csv_row(self):
        if hasattr(self, '__dataclass_fields__'):
            values = [str(getattr(self, field.name)) for field in fields(self)]
        else:
            values = [str(v) for v in self.__dict__.values()]
        return ", ".join(values)




# ============================================================================
# 성과목표: Ⅰ-1 미래형 교육
# ============================================================================
@dataclass
class Goal(BaseDataObject):
    fk: str
    goal_num: str
    goal: str
    id: Optional[int] = None

    def to_dict(self):
        year, ministry = self.fk.split(", ")
        return {
            '사업연도': year,
            '소관': ministry,
            '성과목표번호': self.goal_num,
            '성과목표': self.goal,
        }

# ============================================================================
# 성과목표 Ⅰ-1 미래형 교육
# - (3) 위기관리 계획
# - (4) 기타
# - (5) 주요계획
# ============================================================================
@dataclass
class Etc(BaseDataObject):
    goal_id: str
    etc: str = ""
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '성과목표ID': self.goal_id,
            '기타': self.title,
        }


@dataclass
class RiskManagePlan(BaseDataObject):
    goal_id: str
    risk_manange_plan: str
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '성과목표ID': self.goal_id,
            '위기관리계획': self.title,
        }


@dataclass
class Task(BaseDataObject):
    goal_id: str
    no: str
    title: str
    id: Optional[int] = None

    def to_dict(self):
        return {
            '성과목표ID': self.goal_id,
            '관리과제ID': self.id,
            '관리과제명': self.title,
            '관리과제번호': self.no,
        }

# ============================================================================
# 성과목표 Ⅰ-1 미래형 교육 -> (5)주요계획 
# [① 디지털 전환, ..., ⑥ "관리과제"]
# 
# 관리과제: Ⅰ-1-① 디지털 전환
# - 배경
# - 대상
# - 주요내용(사업 리스트)
# - 계획
# - 재정사업
# - 기대효과
# ============================================================================


class CategoryType(Enum):
    GENERAL = "일반"
    SPECIAL = "특별회계"
    FUND = "기금"


@dataclass
class FinanceBusiness(BaseDataObject):
    task_id: int = 0
    subject: str = ""
    category: CategoryType = CategoryType.GENERAL
    finance_code: str = ""
    subsidy_code: str = ""
    program: str = ""
    unit: str = ""
    sunit: str = ""
    ssunit: list = ""
    ps: str = ""
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '주제': self.subject,
            '회계구분': self.category,
            '회계코드': self.finance_code,
            '교부금코드': self.subsidy_code,
            '프로그램명': self.program,
            '단위사업명': self.unit,
            '내역사업명': self.sunit,
            '비고': self.ps,
            '내내역사업목록': self.ssunit,
        }


@dataclass
class SubTask(BaseDataObject):
    task_id: int = 0
    id: Optional[int] = None

@dataclass
class Background(BaseDataObject):
    task_id: str
    background: str = ""
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '추진배경': self.title,
        }


@dataclass
class Plan(BaseDataObject):
    task_id: str
    plan: str = ""
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '계획': self.plan,
        }

@dataclass
class Target(BaseDataObject):
    task_id: str
    target: str = ""
    related: str = ""
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '수혜자': self.target,
            '이해관계자': self.related,
        }

@dataclass
class Effect(BaseDataObject):
    task_id: str
    effect: str = ""
    id: Optional[int] = None

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '기대효과': self.target,
        }


@dataclass
class Result:
    status: int
    data: dict
    total: int
    success: int
    error_msg: str