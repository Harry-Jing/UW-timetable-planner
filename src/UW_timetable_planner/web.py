import httpx


def get_course_details(course_code: str) -> dict:
    response = httpx.get(
        f"https://course-app-api.planning.sis.uw.edu/api/courses/{course_code}/details"
    )
    return response.json()
