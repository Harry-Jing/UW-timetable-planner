from typing import Optional

from pydantic import BaseModel


class ClassTime(BaseModel):
    start_time: str
    end_time: str
    day: str


class SubSection(BaseModel):
    times: list[ClassTime]


class Lecture(BaseModel):
    quiz: Optional[list[SubSection]] = None
    laboratory: Optional[list[SubSection]] = None
    times: list[ClassTime]


class Course(BaseModel):
    lectures: list[Lecture]
