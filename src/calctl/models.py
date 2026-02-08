'''
Domain models for calctl

This module defines the core data structures used by the calendar
application. These models represent valid domain objects and contain
no I/O or CLI-related logic.
'''

from dataclasses import dataclass
from datetime import datetime, timedelta, date


# @dataclass generate __init__ method, __repr__, __eq__, __hash__, __str__ methods
# frozen=True makes the class immutable
@dataclass(frozen=True)
class Event:
    '''
    Represents a single calendar event.

    An Event is an immutable domain object that contains the essential
    information of a calendar entry, including its time range and
    metadata. All time-based calculations (e.g. start and end datetime)
    are encapsulated within this class.
    '''
    id: str
    title: str
    description: str | None
    date: date  # date is a date object. It's safer than string because it's immutable.
    start_time: str  # because CLI arguments are always strings.
    duration_min: int
    location: str | None
    create_at: datetime
    update_at: datetime  # because datetime is mutable, we use the name update_time instead of update_at.

    def start_dt(self) -> datetime:
        """
        Compute the start datetime of the event.

        Returns:
            datetime: A datetime object representing the start time of the event.
        """
        return datetime.combine(
            self.date, 
            datetime.strptime(self.start_time, '%H:%M').time()  # string parse time: change string to time object. time() only return time not date
        )
    
    def end_dt(self) -> datetime:
        """
        Compute the end datetime of the event.

        Returns:
            datetime: A datetime object representing the end time of the event,
            calculated by adding the duration to the start datetime.
        """
        return self.start_dt() + timedelta(minutes=self.duration_min)  # timedelta is difference between two dates or times. minutes is the unit of time.