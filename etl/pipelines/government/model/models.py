from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Optional

from .id_generator import generate_short_id


class BaseDataObject:
    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.goal}"

    def __repr__(self) -> str:
        return self.__str__()

    def to_tuple(self) -> tuple:
        return tuple(self.get_field_values())
    
    def to_dict(self) -> dict:
        raise NotImplementedError

    @property
    def header(self):
        if hasattr(self, 'to_dict'):
            keys = list(self.to_dict().keys())
        elif hasattr(self, '__dataclass_fields__'):
            keys = [f.name for f in fields(self)]
        else:
            keys = list(self.__dict__.keys())
        return ", ".join(keys)

    @property
    def to_csv_row(self):
        if hasattr(self, '__dataclass_fields__'):
            values = [str(getattr(self, f.name)) for f in fields(self)]
        else:
            values = [str(v) for v in self.__dict__.values()]
        return ", ".join(values)


# ============================================================================
# 성과목표: Ⅰ-1 미래형 교육
# ============================================================================
@dataclass
class Goal(BaseDataObject):
    fk: str
    title: str
    id: str = field(default_factory=generate_short_id)
    # goal_num: str

    def to_dict(self):
        year, ministry = self.fk.split(", ")
        return {
            '사업연도': year,
            '소관': ministry,
            '성과목표번호': self.title,
            'ID': self.id,
            # '성과목표': self.goal,
        }

# ============================================================================
# 성과목표 Ⅰ-1 미래형 교육
# - (3) 위기관리 계획
# - (4) 기타
# - (5) 주요계획
# ============================================================================
@dataclass
class Etc(BaseDataObject):
    fk: str
    content: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '성과목표ID': self.fk,
            '기타': self.content,
            'ID': self.id,
        }


@dataclass
class Risk(BaseDataObject):
    fk: str
    content: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '성과목표ID': self.fk,
            '위기관리계획': self.content,
            'ID': self.id,
        }


@dataclass
class Task(BaseDataObject):
    fk: str
    no: str
    title: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '성과목표ID': self.fk,
            '관리과제명': self.title,
            '관리과제번호': self.no,
            '관리과제ID': self.id,
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
    fk: str
    subject: str
    category: Optional[str] = None
    finance_code: Optional[str] = None
    subsidy_code: Optional[str] = None
    program: Optional[str] = None
    unit: Optional[str] = None
    sunit: Optional[str] = None
    ssunit: Optional[list] = None
    sssunit: Optional[list] = None
    extra: Optional[list] = None
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '관리과제ID': self.fk,
            '주제': self.subject,
            '회계구분': self.category,
            '회계코드': self.finance_code,
            '교부금코드': self.subsidy_code,
            '프로그램명': self.program,
            '단위사업명': self.unit,
            '내역사업명': self.sunit,
            '내내역사업목록': self.ssunit,
            '특교사업목록': self.sssunit,
            '비고': self.extra,
            'ID': self.id,
        }


@dataclass
class SubTask(BaseDataObject):
    fk: str
    sep: str
    title: str
    content: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '관리과제ID': self.fk,
            '분리기호': self.sep,
            '세부과제명': self.title, 
            '세부과제내용': self.content,
            'ID': self.id,
        }

@dataclass
class Background(BaseDataObject):
    fk: str
    content: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '관리과제ID': self.fk,
            '추진배경': self.content,
            'ID': self.id,
        }


@dataclass
class Plan(BaseDataObject):
    fk: str
    content: str
    plan_at: str
    extra: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '관리과제ID': self.fk,
            '계획': self.content,
            '일정': self.plan_at,
            '비고': self.extra,
            'ID': self.id,
        }

@dataclass
class Target(BaseDataObject):
    fk: str
    target_type: Optional[str]
    target: Optional[str]
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '관리과제ID': self.fk,
            '대상자구분': self.target_type,
            '대상자': self.target,
            'ID': self.id,
        }

@dataclass
class Effect(BaseDataObject):
    fk: str
    content: str
    id: str = field(default_factory=generate_short_id)

    def to_dict(self):
        return {
            '관리과제ID': self.fk,
            '기대효과': self.content,
            'ID': self.id,
        }


@dataclass
class Result:
    status: int
    data: dict
    total: int
    success: int
    error_msg: str