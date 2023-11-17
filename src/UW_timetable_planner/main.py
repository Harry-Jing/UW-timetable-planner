import json
from datetime import datetime

import httpx
from data_model import Course, Lecture, ClassTime, SubSection


def get_course_details(course_code: str) -> dict:
    response = httpx.get(
        f"https://course-app-api.planning.sis.uw.edu/api/courses/{course_code}/details"
    )
    return response.json()


def get_course_details_local(course_code: str) -> dict:
    with open(f"tests\\data\\{course_code}.json") as f:
        return json.load(f)


def get_course(course_code: str) -> Course:
    data: dict = get_course_details_local(course_code)
    lectures = []
    subsections = []

    sections = data["courseOfferingInstitutionList"][0]["courseOfferingTermList"][0][
        "activityOfferingItemList"
    ]

    for i in sections:
        code = i["code"]
        times = []

        for meetingDetail in i["meetingDetailsList"]:
            time = meetingDetail["time"].split(" - ")
            start_time = datetime.strptime(time[0], "%I:%M %p").time()
            end_time = datetime.strptime(time[1], "%I:%M %p").time()
            days_str = meetingDetail["days"]
            days = []
            for index in range(len(days_str)):
                try:
                    if days_str[index + 1].islower():
                        days.append(days_str[index] + days_str[index + 1])
                    elif days_str[index].isupper():
                        days.append(days_str[index])
                except IndexError:
                    if days_str[index].isupper():
                        days.append(days_str[index])

            for day in days:
                times.append(
                    ClassTime(start_time=start_time, end_time=end_time, day=day)
                )

        if len(code) == 1:
            lectures.append(Lecture(code=code, times=times))
        if len(code) == 2:
            subsection = SubSection(
                code=code, times=times, type=i["activityOfferingType"]
            )
            for lecture in lectures:
                if lecture.code == subsection.code[0]:
                    lecture.add_subsection(subsection)

    # print(lectures)


if __name__ == "__main__":
    get_course("PHYS 121")
