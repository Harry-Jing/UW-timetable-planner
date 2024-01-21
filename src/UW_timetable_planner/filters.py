from datetime import time
from itertools import product

from pydantic import BaseModel

from .utils import check_conflict
from .course import Section, Weekday, ClassTime


class SectionFilters(BaseModel):
    """Filters for Section objects."""

    exclueded_times: list[ClassTime] = []

    @classmethod
    def test_filter(cls):
        exclueded_times = [
            ClassTime(
                start_time=time(6, 30), end_time=time(12, 30), day=Weekday.MONDAY
            ),
            ClassTime(
                start_time=time(6, 30), end_time=time(12, 30), day=Weekday.TUESDAY
            ),
            ClassTime(
                start_time=time(6, 30), end_time=time(12, 30), day=Weekday.WEDNESDAY
            ),
            ClassTime(
                start_time=time(6, 30), end_time=time(12, 30), day=Weekday.THURSDAY
            ),
            ClassTime(
                start_time=time(6, 30), end_time=time(12, 30), day=Weekday.FRIDAY
            ),
        ]

        return cls(exclueded_times=exclueded_times)

    def check_conflict(self, section: Section) -> bool:
        """Check if a section has conflict with this filter.
        Return True if there is a conflict, False otherwise."""

        # Check if any of the section times conflicts with any of the excluded times
        if any(
            check_conflict(time1, time2)
            for time1, time2 in product(section.times, self.exclueded_times)
        ):
            return True
        return False
