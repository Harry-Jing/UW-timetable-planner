from pydantic import BaseModel


class ClassTime(BaseModel):
    start_time: str
    end_time: str
    day: str


class SubSection(BaseModel):
    times: list[ClassTime]


class Lecture(BaseModel):
    quiz: list[SubSection] = []
    laboratory: list[SubSection] = []
    times: list[ClassTime]


class Course(BaseModel):
    lectures: list[Lecture]
