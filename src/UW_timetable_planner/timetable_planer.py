from typing import Self
from itertools import product

from pydantic import BaseModel

from .course import Course, Section
from .filters import SectionFilters
from .timetable import (
    Timetable,
    ScheduledCourse,
    ScheduledSubsection,
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
            if first_course.code == "MATH 207" and primary_section.code == "D":
                pass
            if not self.feasible(primary_section, current_timetable):
                continue

            if not primary_section.subsections:
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

            for subsections_group in product(*primary_section.subsections.values()):
                # TODO: Check if there is any conflict between subsections_group
                if any(
                    not self.feasible(section, current_timetable)
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
                            ScheduledSubsection.from_subsection(subsection)
                            for subsection in subsections_group
                        ],
                    )
                )
                self._explore_course(remaining_courses, current_timetable)
                current_timetable.pop()
                continue

    def feasible(self, section: Section, timetable: Timetable) -> bool:
        """Check if a section is feasible under this filter.
        Return True if it is feasible, False otherwise."""

        return self.section_filters.feasible(
            section
        ) and not timetable.check_time_conflict(section)

    @classmethod
    def build(
        cls, course_codes: list[str], section_filters: SectionFilters = SectionFilters()
    ) -> Self:
        courses = [Course.from_course_code(course_code) for course_code in course_codes]
        return cls(courses=courses, section_filters=section_filters)
