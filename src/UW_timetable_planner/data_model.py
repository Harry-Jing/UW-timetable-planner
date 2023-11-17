from datetime import time

from pydantic import BaseModel


class ClassTime(BaseModel):
    start_time: time
    end_time: time
    day: str


class SubSection(BaseModel):
    code: str
    times: list[ClassTime]
    type: str


class Lecture(BaseModel):
    code: str
    quizzes: list[SubSection] = []
    laboratories: list[SubSection] = []
    times: list[ClassTime]

    def add_subsection(self, subsection):
        if subsection.type == "quiz":
            self.quizzes.append(subsection)
        if subsection.type == "laboratory":
            self.laboratories.append(subsection)


class Course(BaseModel):
    lectures: list[Lecture]
