import re
import asyncio
from enum import IntEnum
from typing import Self, Union, Literal
from datetime import time, datetime

import httpx
from pydantic import BaseModel


class Weekday(IntEnum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

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
    def from_data(cls, data: dict) -> list[Self]:
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


class Location(BaseModel):
    building: str
    room: str


class Section(BaseModel):
    code: str

    times: list[ClassTime]

    @classmethod
    def from_data(cls, data: dict) -> Union["Lecture", "Quiz", "Laboratory"]:
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
    pass


class Quiz(SubSection):
    pass


class Laboratory(SubSection):
    pass


class Lecture(Section):
    quizzes: list[Quiz] | None = None
    laboratories: list[Laboratory] | None = None

    def add_subsection(self, subsection: SubSection):
        if isinstance(subsection, Quiz):
            if self.quizzes is None:
                self.quizzes = []
            self.quizzes.append(subsection)
            return
        if isinstance(subsection, Laboratory):
            if self.laboratories is None:
                self.laboratories = []
            self.laboratories.append(subsection)
            return

        raise ValueError(f"Invalid subsection type {type(subsection)}")


class Course(BaseModel):
    code: str
    credit: int
    course_title: str
    lectures: list[Lecture]

    @classmethod
    def from_data(cls, data: dict) -> Self:
        course_summary_details: dict = data["courseSummaryDetails"]
        section_items: list[dict] = data["courseOfferingInstitutionList"][0][
            "courseOfferingTermList"
        ][0]["activityOfferingItemList"]

        sections = [Section.from_data(i) for i in section_items]

        lectures = []
        for section in sections:
            if not isinstance(section, Lecture):
                continue

            lectures.append(section)

            for subsection in sections:
                if isinstance(subsection, SubSection) and subsection.code.startswith(
                    section.code
                ):
                    section.add_subsection(subsection)

        return cls(
            code=f"{course_summary_details['subjectArea']} {course_summary_details['courseNumber']}",
            credit=course_summary_details["credit"],
            course_title=course_summary_details["courseTitle"],
            lectures=lectures,
        )

    @classmethod
    def from_course_code(cls, course_code: str) -> Self:
        response = httpx.get(
            f"https://course-app-api.planning.sis.uw.edu/api/courses/{course_code}/details"
        )

        return cls.from_data(response.json())
