import sys
from enum import Enum
from typing import TypedDict, Union

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired


# class ParsedInfo(TypedDict):
#     event: str  # "register_job", "create_data", "update_data"
#     data: dict


class Goal(TypedDict):
    fk: str
    id: str
    goal_num: str
    goal: str


class Etc(TypedDict):
    id: str
    fk: str
    content: NotRequired[str]


class Risk(TypedDict):
    id: str
    fk: str
    content: str


class Task(TypedDict):
    fk: str
    id: str
    no: str
    title: str


# class CategoryType(Enum):
#     GENERAL = "일반"
#     SPECIAL = "특별회계"
#     FUND = "기금"


class FinanceBusiness(TypedDict):
    id: NotRequired[int]
    fk: NotRequired[int]
    subject: NotRequired[str]
    category: NotRequired[str]
    subsidy_code: NotRequired[str]
    program: NotRequired[str]
    unit: NotRequired[str]
    sunit: NotRequired[str]
    ssunit: NotRequired[list]
    ps: NotRequired[list]


class SubTask(TypedDict):
    id: NotRequired[int]
    fk: NotRequired[int]
    sep: NotRequired[str]
    title: NotRequired[str]
    content: str


class Background(TypedDict):
    id: str
    fk: str
    content: NotRequired[str]


class Plan(TypedDict):
    id: str
    fk: str
    content: NotRequired[str]

class Target(TypedDict):
    id: str
    fk: str
    target: NotRequired[str]
    related: NotRequired[str]

class Effect(TypedDict):
    id: str
    fk: str
    content: NotRequired[str]


class Result(TypedDict):
    status: int
    data: dict
    total: int
    success: int
    error_msg: str
