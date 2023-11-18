import re
from enum import IntEnum
from typing import Any, Literal
from datetime import time, datetime

from pydantic import BaseModel


def get_course_details_local(course_code: str) -> dict:
    import json

    with open(f"tests/data/{course_code}.json") as f:
        return json.load(f)


class Weekday(IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5

    @classmethod
    def from_short_name(cls, short_name: Literal["M", "T", "W", "Th", "F"]):
        match short_name:
            case "M":
                return cls.MONDAY
            case "T":
                return cls.TUESDAY
            case "W":
                return cls.WEDNESDAY
            case "Th":
                return cls.THURSDAY
            case "F":
                return cls.FRIDAY
            case _:
                raise ValueError(f"{short_name} is not a valid weekday short name")


class ClassTime(BaseModel):
    start_time: time
    end_time: time
    day: Weekday

    @classmethod
    def from_data(cls, data: dict) -> list["ClassTime"]:
        times = []

        time = data["time"].split(" - ")
        start_time = datetime.strptime(time[0], "%I:%M %p").time()
        end_time = datetime.strptime(time[1], "%I:%M %p").time()

        days = re.compile(r"M|T(?!h)|Th|W|F").findall(data["days"])

        for day in days:
            times.append(
                cls(
                    start_time=start_time,
                    end_time=end_time,
                    day=Weekday.from_short_name(day),
                )
            )

        return times


class Section(BaseModel):
    code: str
    times: list[ClassTime]

    @classmethod
    def from_data(cls, data: dict) -> "Section":
        code = data["code"]

        times = []
        for meetingDetail in data["meetingDetailsList"]:
            times.extend(ClassTime.from_data(meetingDetail))

        if len(code) == 1:
            return Lecture(code=code, times=times)
        if len(code) == 2 and data["activityOfferingType"] == "quiz":
            return Quiz(code=code, times=times)
        if len(code) == 2 and data["activityOfferingType"] == "laboratory":
            return Laboratory(code=code, times=times)

        raise ValueError(f"Invalid section code {code}")


class SubSection(Section):
    ...


class Quiz(SubSection):
    ...


class Laboratory(SubSection):
    ...


class Lecture(Section):
    quizzes: list[Quiz] = []
    laboratories: list[Laboratory] = []

    def add_subsection(self, subsection: Laboratory | Quiz):
        if isinstance(subsection, Quiz):
            self.quizzes.append(subsection)
        if isinstance(subsection, Laboratory):
            self.laboratories.append(subsection)


class Course(BaseModel):
    code: str
    lectures: list[Lecture]

    @classmethod
    def corse_code(cls, course_code: str) -> "Course":
        data: dict = get_course_details_local(course_code)
        sections = []

        for i in data["courseOfferingInstitutionList"][0]["courseOfferingTermList"][0][
            "activityOfferingItemList"
        ]:
            sections.append(Section.from_data(i))

        lectures = []
        for section in sections:
            if isinstance(section, Lecture):
                lectures.append(section)
                for subsection in sections:
                    if isinstance(subsection, Quiz) or isinstance(
                        subsection, Laboratory
                    ):
                        section.add_subsection(subsection)

        return cls(code=course_code, lectures=lectures)


if __name__ == "__main__":
    from rich import print

    course = Course.corse_code("CSE 122")
    print(course)
