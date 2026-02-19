from dataclasses import dataclass

@dataclass
class DateRange:
    """Model for date ranges of years"""
    start_year: int
    end_year: int