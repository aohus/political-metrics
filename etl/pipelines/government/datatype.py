import random
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any


class DataObjectMixin:
    """모든 데이터 객체가 공유하는 공통 기능"""

    def __post_init__(self):
        self.id = random.SystemRandom()

    @property
    def to_csv_row(self) -> str:
        if hasattr(self, '__dataclass_fields__'):
            values = [str(getattr(self, field.name)) for field in fields(self)]
        else:
            values = [str(v) for v in self.__dict__.values()]
        return ", ".join(values)

    @property 
    def header(self) -> str:
        if hasattr(self, '__dataclass_fields__'):
            keys = [field.name for field in fields(self)]
        else:
            keys = list(self.__dict__.keys())
        return ", ".join(keys)

    def get_field_values(self) -> list[Any]:
        if hasattr(self, '__dataclass_fields__'):
            return [getattr(self, field.name) for field in fields(self)]
        else:
            return list(self.__dict__.values())

    def get_field_names(self) -> list[str]:
        if hasattr(self, '__dataclass_fields__'):
            return [field.name for field in fields(self)]
        else:
            return list(self.__dict__.keys())


class BaseDataObject(DataObjectMixin):
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.to_str})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_tuple(self) -> tuple:
        return tuple(self.get_field_values())


### 성과목표 [Ⅰ-1] 형식
@dataclass
class Goal(BaseDataObject):
    fk: str
    id: str
    goal_num: str
    goal: str

    def to_dict(self):
        year, ministry = self.fk.split(", ")
        return {
            '사업연도': year,
            '소관': ministry,
            '성과목표번호': self.goal_num,
            '성과목표': self.goal,
        }
    
    @property
    def to_str(self):
        return ", ".join([str(v) for v in self.__dict__.values()])
    
    @property
    def header(self):
        return ", ".join([str(k) for k in self.__dict__.keys()])
    

### 성과목표 Ⅰ-1: (3) 위기관리 계획, (4) 기타, (5) 주요계획
@dataclass
class Etc(BaseDataObject):
    id: str
    goal_id: str
    etc: str = ""

    def to_dict(self):
        return {
            'ID': self.id,
            '성과목표ID': self.goal_id,
            '기타': self.title,
        }


@dataclass
class RiskManagePlan(BaseDataObject):
    id: str
    goal_id: str
    risk_manange_plan: str

    def to_dict(self):
        return {
            'ID': self.id,
            '성과목표ID': self.goal_id,
            '위기관리계획': self.title,
        }


@dataclass
class Task(BaseDataObject):
    goal_id: str
    id: str
    no: str
    title: str

    def to_dict(self):
        return {
            '성과목표ID': self.goal_id,
            '관리과제ID': self.id,
            '관리과제명': self.title,
            '관리과제번호': self.no,
        }


### 성과목표 Ⅰ-1: (5)주요계획 [①과제, ..., ⑥과제]
### Ⅰ-1-① 배경, 대상, 주요내용(사업 리스트), 계획, 재정사업, 기대효과
class CategoryType(Enum):
    GENERAL = "일반"
    SPECIAL = "특별회계"
    FUND = "기금"


@dataclass
class FinanceBusiness(BaseDataObject):
    id: int = 0
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
    id: int = 0
    task_id: int = 0


@dataclass
class Background(BaseDataObject):
    id: str
    task_id: str
    background: str = ""

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '추진배경': self.title,
        }

@dataclass
class Plan(BaseDataObject):
    id: str
    task_id: str
    plan: str = ""

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '계획': self.plan,
        }

@dataclass
class Target(BaseDataObject):
    id: str
    task_id: str
    target: str = ""
    related: str = ""

    def to_dict(self):
        return {
            'ID': self.id,
            '관리과제ID': self.task_id,
            '수혜자': self.target,
            '이해관계자': self.related,
        }

@dataclass
class Effect(BaseDataObject):
    id: str
    task_id: str
    effect: str = ""

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