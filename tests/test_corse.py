import json

from UW_timetable_planner.course import Course, Lecture

test_course_codes = ["CSE 123" "PHYS 121"]


def test_course_CSE_123_online():
    course = Course.from_course_code("CSE 123")

    assert isinstance(course, Course)

    assert course.code == "CSE 123"
    assert course.credit == 4
    assert course.course_title == "Introduction to Computer Programming III"

    for i in course.lectures:
        assert isinstance(i, Lecture)


def test_course_PHYS_121_local():
    with open("tests/data/PHYS 121.json") as f:
        data = json.load(f)

    course = Course.from_data(data)

    assert isinstance(course, Course)

    assert course.code == "PHYS 121"
    assert course.credit == 5
    assert course.course_title == "Mechanics"

    for i in course.lectures:
        assert isinstance(i, Lecture)
