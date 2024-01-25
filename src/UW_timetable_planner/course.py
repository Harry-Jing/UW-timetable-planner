import re
import asyncio
from enum import IntEnum, StrEnum
from typing import Self, Literal
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
    def from_short_name(
        cls, short_name: Literal["M", "T", "W", "Th", "F"]
    ) -> "Weekday":
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


class SectionType(StrEnum):
    LECTURE = "lecture"
    QUIZ = "quiz"
    LABORATORY = "laboratory"

    @classmethod
    def from_str(cls, string: str) -> "SectionType":
        match string:
            case "lecture":
                return cls.LECTURE
            case "quiz":
                return cls.QUIZ
            case "laboratory":
                return cls.LABORATORY
            case _:
                raise ValueError(f"{string} is not a valid section type")


class LearningFormat(StrEnum):
    IN_PERSON = "In-person"
    SYNCHRONOUS_ONLINE = "Synchronous Online"
    ASYNCHRONOUS_ONLINE = "Asynchronous Online"
    HYBRID = "Hybrid"

    @classmethod
    def from_str(cls, string: str) -> "LearningFormat":
        match string:
            case "In-person":
                return cls.IN_PERSON
            case "Synchronous Online":
                return cls.SYNCHRONOUS_ONLINE
            case "Asynchronous Online":
                return cls.ASYNCHRONOUS_ONLINE
            case "Hybrid":
                return cls.HYBRID
            case _:
                raise ValueError(f"{string} is not a valid learning format")


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


class MeetingDetails(BaseModel):
    class_time: ClassTime
    location: Location | None = None

    @classmethod
    def from_data(cls, data: dict) -> list[Self]:
        """Return a list of MeetingDetails from a dict of meeting details data
        If it is a TBA meeting, return an empty list"""
        if data["time"] is None:
            return []

        times = ClassTime.from_data(data)
        location = None
        if data["building"]:
            location = Location(
                building=data["building"],
                room=data["room"],
            )
        return [cls(class_time=time, location=location) for time in times]


class SectionStatus(BaseModel):
    enroll_maximum: int
    enroll_count: int

    @property
    def is_full(self) -> bool:
        return self.enroll_maximum == self.enroll_count

    @property
    def remaining(self) -> int:
        return self.enroll_maximum - self.enroll_count


class Section(BaseModel):
    code: str
    primary_section_code: str
    SLN: int
    type: SectionType
    learning_format: LearningFormat
    details_of_meetings: list[MeetingDetails]
    instructors: list[str]
    status: SectionStatus
    is_add_code_required: bool

    @classmethod
    def from_data(cls, data: dict) -> Self:
        code = data["code"]
        primary_section_code = data["primaryActivityOfferingCode"]
        SLN = int(data["registrationCode"])
        section_type = SectionType.from_str(data["activityOfferingType"])
        learning_format = LearningFormat.from_str(data["onlineLearningText"])
        is_add_code_required = data["addCodeRequired"]
        instructors = [d["name"] for d in data["allInstructors"]]
        status = SectionStatus(
            enroll_maximum=data["enrollMaximum"],
            enroll_count=data["enrollCount"],
        )

        meetings_details = []
        for meeting_detail in data["meetingDetailsList"]:
            meetings_details.extend(MeetingDetails.from_data(meeting_detail))

        return cls(
            code=code,
            primary_section_code=primary_section_code,
            SLN=SLN,
            type=section_type,
            learning_format=learning_format,
            details_of_meetings=meetings_details,
            instructors=instructors,
            status=status,
            is_add_code_required=is_add_code_required,
        )


class SubSection(Section):
    pass


class PrimarySection(Section):
    sub_sections: dict[SectionType, list[SubSection]] = {}

    def add_subsection(self, subsection: SubSection) -> None:
        if subsection.type not in self.sub_sections:
            self.sub_sections[subsection.type] = []
        self.sub_sections[subsection.type].append(subsection)


class Lecture(PrimarySection):
    pass


class Course(BaseModel):
    code: str
    credit: int
    course_title: str
    primary_sections: list[PrimarySection]

    @classmethod
    def from_data(cls, data: dict) -> Self:
        course_summary_details: dict = data["courseSummaryDetails"]
        section_items: list[dict] = data["courseOfferingInstitutionList"][0][
            "courseOfferingTermList"
        ][0]["activityOfferingItemList"]

        primary_sections = []
        primary_section = None
        for section in section_items:
            if section["primary"]:
                primary_section = PrimarySection.from_data(section)
                primary_sections.append(primary_section)
            else:
                if primary_section is None:
                    raise ValueError("No primary section found")
                subsection = SubSection.from_data(section)
                if subsection.primary_section_code != primary_section.code:
                    raise ValueError("Subsection does not match primary section")
                primary_section.add_subsection(subsection)

        return cls(
            code=f"{course_summary_details['subjectArea']} {course_summary_details['courseNumber']}",
            credit=course_summary_details["credit"],
            course_title=course_summary_details["courseTitle"],
            primary_sections=primary_sections,
        )

    @classmethod
    def from_course_code(cls, course_code: str) -> Self:
        response = httpx.get(
            f"https://course-app-api.planning.sis.uw.edu/api/courses/{course_code}/details"
        )

        return cls.from_data(response.json())

    @classmethod
    async def from_course_code_async(cls, course_code: str) -> Self:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://course-app-api.planning.sis.uw.edu/api/courses/{course_code}/details"
            )

        return cls.from_data(response.json())


if __name__ == "__main__":
    from rich import print

    course = Course.from_course_code("MATH 126")
    print(course)
