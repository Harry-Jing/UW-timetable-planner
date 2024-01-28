from datetime import time
from itertools import product

from pydantic import BaseModel

from .utils import check_time_conflict
from .course import Section, Weekday, ClassTime, LearningFormat


class SectionFilters(BaseModel):
    """Filters for Section objects."""

    exclueded_times: list[ClassTime] = []
    is_check_require_add_codes: bool = False
    is_check_full: bool = False
    is_check_online: bool = False
    consider_time_mask_flag: bool = False  # TODO: Implement this

    def check_time_conflict(self, section: Section) -> bool:
        """Check if a section has conflict with this filter.
        Return True if there is a conflict, False otherwise."""

        # TODO: Optimise it
        if any(
            check_time_conflict(details.class_time, time2)
            for details, time2 in product(
                section.details_of_meetings, self.exclueded_times
            )
        ):
            return True
        return False

    def feasible(self, section: Section) -> bool:
        """Check if a section is feasible under this filter.
        Return True if it is feasible, False otherwise."""

        if self.check_time_conflict(section):
            return False
        if self.is_check_require_add_codes and section.is_add_code_required:
            return False
        if self.is_check_full and section.status.is_full:
            return False
        if self.is_check_online and section.learning_format.is_online:
            return False

        return True
