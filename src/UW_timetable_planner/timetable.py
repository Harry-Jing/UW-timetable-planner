from typing import Self

from pydantic import BaseModel

from .utils import check_conflict
from .course import Quiz, Lecture, Section, Laboratory, SubSection


class ScheduledSection(Section):
    @classmethod
    def from_section(cls, section: Section) -> Self:
        return cls(code=section.code, times=section.times)


class ScheduledLecture(ScheduledSection):
    @classmethod
    def from_lecture(cls, lecture: Lecture) -> Self:
        return cls.from_section(lecture)


class ScheduledSubSection(ScheduledSection, SubSection):
    pass


class ScheduledQuiz(ScheduledSubSection, Quiz):
    @classmethod
    def from_quiz(cls, subsection: SubSection) -> Self:
        return cls.from_section(subsection)


class ScheduledLaboratory(ScheduledSubSection, Laboratory):
    @classmethod
    def from_laboratory(cls, subsection: SubSection) -> Self:
        return cls.from_section(subsection)


class ScheduledCourse(BaseModel):
    code: str
    lecture: ScheduledLecture
    quiz: ScheduledQuiz | None = None
    laboratory: ScheduledLaboratory | None = None

    def check_conflict(self, section: Section) -> bool:
        """Check if a section has conflict with this scheduled course.
        Return True if there is a conflict, False otherwise."""
        for time1 in section.times:
            if any(check_conflict(time1, time2) for time2 in self.lecture.times):
                return True
            if self.quiz and any(
                check_conflict(time1, time2) for time2 in self.quiz.times
            ):
                return True
            if self.laboratory and any(
                check_conflict(time1, time2) for time2 in self.laboratory.times
            ):
                return True
        return False


class Timetable(BaseModel):
    timetable: list[ScheduledCourse]

    def pop(self):
        self.timetable.pop()

    def check_conflict(self, section: Section) -> bool:
        for scheduled_course in self.timetable:
            if scheduled_course.check_conflict(section):
                return True
        return False

    def add_scheduled_course(self, scheduled_course: ScheduledCourse):
        self.timetable.append(scheduled_course)
