import sys
from enum import Enum
from typing import TypedDict, Union

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired


class Goal(TypedDict):
    fk: str
    id: str
    goal_num: str
    goal: str

class Etc(TypedDict):
    id: str
    goal_id: str
    etc: NotRequired[str]


class RiskManagePlan(TypedDict):
    id: str
    goal_id: str
    risk_manange_plan: str


class Task(TypedDict):
    goal_id: str
    id: str
    no: str
    title: str


class CategoryType(Enum):
    GENERAL = "일반"
    SPECIAL = "특별회계"
    FUND = "기금"


class FinanceBusiness(TypedDict):
    id: NotRequired[int]
    task_id: NotRequired[int]
    subject: NotRequired[str]
    category: NotRequired[CategoryType]
    finance_code: NotRequired[str]
    subsidy_code: NotRequired[str]
    program: NotRequired[str]
    unit: NotRequired[str]
    sunit: NotRequired[str]
    ssunit: NotRequired[list]
    ps: NotRequired[str]


class SubTask(TypedDict):
    id: NotRequired[int]
    task_id: NotRequired[int]


class Background(TypedDict):
    id: str
    task_id: str
    background: NotRequired[str]


class Plan(TypedDict):
    id: str
    task_id: str
    plan: NotRequired[str]

class Target(TypedDict):
    id: str
    task_id: str
    target: NotRequired[str]
    related: NotRequired[str]

class Effect(TypedDict):
    id: str
    task_id: str
    effect: NotRequired[str]


class Result(TypedDict):
    status: int
    data: dict
    total: int
    success: int
    error_msg: str
