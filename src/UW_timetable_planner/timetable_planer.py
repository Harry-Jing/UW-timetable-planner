from typing import Self
from itertools import product

from pydantic import BaseModel

from .course import Course, Section
from .filters import SectionFilters
from .timetable import (
    Timetable,
    ScheduledCourse,
    ScheduledSubSection,
    ScheduledPrimarySection,
)


class TimetablePlaner(BaseModel):
    courses: list[Course]
    schedule: list[Timetable] = []
    section_filters: SectionFilters = SectionFilters()

    def find_all_possible_timetable(self) -> None:
        courses = self.courses.copy()
        self._explore_course(courses=courses, current_timetable=Timetable(timetable=[]))

    def _explore_course(self, courses: list[Course], current_timetable: Timetable):
        if not courses:
            self.schedule.append(current_timetable.model_copy(deep=True))
            return

        first_course, remaining_courses = courses[0], courses[1:]

        for primary_section in first_course.primary_sections:
            if self.check_conflict(primary_section, current_timetable):
                continue

            if not primary_section.sub_sections:
                current_timetable.add_scheduled_course(
                    ScheduledCourse(
                        code=first_course.code,
                        primary_section=ScheduledPrimarySection.from_primary_section(
                            primary_section
                        ),
                    )
                )
                self._explore_course(remaining_courses, current_timetable)
                current_timetable.pop()
                continue

            for subsections_group in product(*primary_section.sub_sections.values()):
                # TODO: Check if there is any conflict between subsections_group
                if any(
                    self.check_conflict(section, current_timetable)
                    for section in subsections_group
                ):
                    continue

                current_timetable.add_scheduled_course(
                    ScheduledCourse(
                        code=first_course.code,
                        primary_section=ScheduledPrimarySection.from_primary_section(
                            primary_section
                        ),
                        subsection=[
                            ScheduledSubSection.from_subsection(subsection)
                            for subsection in subsections_group
                        ],
                    )
                )
                self._explore_course(remaining_courses, current_timetable)
                current_timetable.pop()
                continue

    def check_conflict(self, section: Section, timetable: Timetable) -> bool:
        return self.section_filters.check_conflict(section) or timetable.check_conflict(
            section
        )

    @classmethod
    def build(
        cls, course_codes: list[str], section_filters: SectionFilters = SectionFilters()
    ) -> Self:
        courses = [Course.from_course_code(course_code) for course_code in course_codes]
        return cls(courses=courses, section_filters=section_filters)


if __name__ == "__main__":
    from datetime import time

    from rich import print

    from .course import Weekday, ClassTime

    tp = TimetablePlaner.build(
        course_codes=["MATH 207", "MATH 208", "CSE 123", "MATH 126"],
        section_filters=SectionFilters(
            exclueded_times=[
                ClassTime(
                    start_time=time(6, 30), end_time=time(12, 30), day=Weekday.MONDAY
                ),
                ClassTime(
                    start_time=time(6, 30), end_time=time(13, 30), day=Weekday.TUESDAY
                ),
                ClassTime(
                    start_time=time(6, 30), end_time=time(12, 30), day=Weekday.WEDNESDAY
                ),
                ClassTime(
                    start_time=time(6, 30), end_time=time(13, 30), day=Weekday.THURSDAY
                ),
                ClassTime(
                    start_time=time(6, 30), end_time=time(12, 30), day=Weekday.FRIDAY
                ),
            ]
        ),
    )

    tp.find_all_possible_timetable()

    print(tp.schedule)
    print(len(tp.schedule))
