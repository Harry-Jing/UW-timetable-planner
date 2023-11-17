import httpx

from .data_model import Course, Lecture


def get_course_details(course_code: str) -> dict:
    response = httpx.get(
        f"https://course-app-api.planning.sis.uw.edu/api/courses/{course_code}/details"
    )
    return response.json()


def get_course(course_code: str) -> Course:
    data: dict = get_course_details(course_code)
    lectures = []

    sections = data["courseOfferingInstitutionList"][0]["courseOfferingTermList"][0][
        "activityOfferingItemList"
    ]

    for i in sections:
        ...
