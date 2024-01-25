from datetime import time
from itertools import product

from pydantic import BaseModel

from .utils import check_conflict
from .course import Section, Weekday, ClassTime


# TODO: Split filters into excluded and included filters
class SectionFilters(BaseModel):
    """Filters for Section objects."""

    exclueded_times: list[ClassTime] = []
    included_times: list[ClassTime] = []

    def check_conflict(self, section: Section) -> bool:
        """Check if a section has conflict with this filter.
        Return True if there is a conflict, False otherwise."""

        # Check if any of the section times conflicts with any of the excluded times
        # TODO: Optimise it
        if any(
            check_conflict(details.class_time, time2)
            for details, time2 in product(
                section.details_of_meetings, self.exclueded_times
            )
        ):
            return True
        return False
