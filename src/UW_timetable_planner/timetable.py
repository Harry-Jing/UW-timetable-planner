from typing import Self

from pydantic import BaseModel

from .utils import check_time_conflict
from .course import Section, Subsection, PrimarySection


class ScheduledSection(Section):
    @classmethod
    def from_section(cls, section: Section) -> Self:
        return cls(**section.model_dump())


class ScheduledPrimarySection(ScheduledSection):
    # TODO: Optimise this
    @classmethod
    def from_primary_section(cls, primary_section: PrimarySection) -> Self:
        return cls.from_section(primary_section)


class ScheduledSubsection(ScheduledSection):
    @classmethod
    def from_subsection(cls, subsection: Subsection) -> Self:
        return cls.from_section(subsection)


class ScheduledCourse(BaseModel):
    code: str
    primary_section: ScheduledPrimarySection
    subsection: list[ScheduledSubsection] = []

    def check_time_conflict(self, section: Section) -> bool:
        """Check if a section has conflict with this scheduled course.
        Return True if there is a conflict, False otherwise."""
        for d1 in section.details_of_meetings:
            if any(
                check_time_conflict(d1.class_time, d2.class_time)
                for d2 in self.primary_section.details_of_meetings
            ):
                return True

            for subsection in self.subsection:
                if any(
                    check_time_conflict(d1.class_time, d2.class_time)
                    for d2 in subsection.details_of_meetings
                ):
                    return True
        return False


class Timetable(BaseModel):
    timetable: list[ScheduledCourse]

    def pop(self) -> None:
        self.timetable.pop()

    def check_time_conflict(self, section: Section) -> bool:
        """Check if a section has conflict with this timetable.
        Return True if there is a conflict, False otherwise."""

        return any(
            scheduled_course.check_time_conflict(section)
            for scheduled_course in self.timetable
        )

    def add_scheduled_course(self, scheduled_course: ScheduledCourse) -> None:
        self.timetable.append(scheduled_course)
