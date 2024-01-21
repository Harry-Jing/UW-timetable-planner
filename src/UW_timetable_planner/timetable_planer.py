from typing import Self

from pydantic import BaseModel

from .course import Quiz, Course, Lecture, Section, Laboratory
from .filters import SectionFilters
from .timetable import (
    Timetable,
    ScheduledQuiz,
    ScheduledCourse,
    ScheduledLecture,
    ScheduledLaboratory,
)


class TimetablePlaner(BaseModel):
    courses: list[Course]
    schedule: list[Timetable] = []
    section_filters: SectionFilters = SectionFilters()

    def find_all_possible_timetable(self):
        courses = self.courses.copy()
        self._explore_course(courses=courses, current_timetable=Timetable(timetable=[]))

    def _explore_course(self, courses: list[Course], current_timetable: Timetable):
        if not courses:
            self.schedule.append(current_timetable.model_copy(deep=True))
            return

        first_course, remaining_courses = courses[0], courses[1:]

        for lecture in first_course.lectures:
            if self.section_filters.check_conflict(
                lecture
            ) or current_timetable.check_conflict(lecture):
                continue

            if not lecture.quizzes:
                current_timetable.add_scheduled_course(
                    ScheduledCourse(
                        code=first_course.code,
                        lecture=ScheduledLecture.from_section(lecture),
                    )
                )
                self._explore_course(remaining_courses, current_timetable)
                current_timetable.pop()
                continue

            for quiz in lecture.quizzes:
                if self.section_filters.check_conflict(
                    quiz
                ) or current_timetable.check_conflict(quiz):
                    continue
                current_timetable.add_scheduled_course(
                    ScheduledCourse(
                        code=first_course.code,
                        lecture=ScheduledLecture.from_section(lecture),
                        quiz=ScheduledQuiz.from_section(quiz),
                    )
                )
                self._explore_course(remaining_courses, current_timetable)
                current_timetable.pop()
            else:
                continue

    @classmethod
    def build(
        cls, course_codes: list[str], section_filters: SectionFilters = SectionFilters()
    ) -> Self:
        courses = [Course.from_course_code(course_code) for course_code in course_codes]
        return cls(courses=courses, section_filters=section_filters)
