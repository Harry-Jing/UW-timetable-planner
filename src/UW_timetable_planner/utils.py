from .course import ClassTime


def check_time_conflict(time1: ClassTime, time2: ClassTime) -> bool:
    """Check if two ClassTime objects have conflict.
    Return True if there is a conflict, False otherwise."""
    if time1.day != time2.day:
        return False
    return not (
        time1.end_time <= time2.start_time or time2.end_time <= time1.start_time
    )
