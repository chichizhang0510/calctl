'''
Service layer for the calendar application.

This module contains the business logic for the calendar application.
It handles the interaction between the CLI and the data store.
'''

from pathlib import Path
from datetime import datetime, date
from secrets import token_hex
from .models import Event
from .store import JsonEventStore
from .errors import InvalidInputError, NotFoundError, StorageError


class CalendarService:
    '''
    Service layer for the calendar application.

    This class contains the business logic for the calendar application.
    It handles the interaction between the CLI and the data store.
    '''
    def __init__(self, store: JsonEventStore):
        self.store = store
    
    def add_event(self, 
            title: str, 
            date_str: str,
            time_str: str,
            duration: int,
            description: str | None = None,
            location: str | None = None) -> Event:
        '''
        Add a new event to the calendar.

        Args:
            title: The title of the event.
            date_str: The date of the event.
            time_str: The time of the event.
            duration: The duration of the event.
        '''
        # parse and validate input arguments
        title = (title or "").strip()
        if not title:
            raise InvalidInputError("Title is required")

        d = self._parse_date(date_str)
        t = self._normalize_time(time_str)
        dur = self._validate_duration(duration)
        now = datetime.now()
        
        # create a new event object
        event = Event(
            id=self._new_event_id(),
            title=title,
            description=(description.strip() if description else None),
            date=d,
            start_time=t,
            duration_min=dur,
            location=(location.strip() if location else None),
            create_at=now,
            update_at=now,
        )

        # why must the event end on the same day as the start? because logic is easier to understand and implement.
        if event.end_dt().date() != event.start_dt().date():
            raise InvalidInputError("Event cannot cross midnight (duration too long)")

        # add the event to the store
        self.store.add(event)
        return event
    
    def list_events(self) -> list[Event]:
        '''
        List all events in the calendar.

        Returns:
            list[Event]: A list of all events in the calendar.
        '''
        return self.store.list_all()
    
    def show_event(self, event_id: str) -> Event:
        '''
        Show an event by its id.

        Args:
            event_id: The id of the event.

        Returns:
            Event: The event.
        '''
        e = self.store.get_by_id(event_id)
        if e is None:
            raise NotFoundError(f"Event with id {event_id} not found")
        return e
    
    def delete_event(self, event_id: str) -> None:
        '''
        Delete an event by its id.

        Args:
            event_id: The id of the event.

        Returns:
            None
        '''
        ok = self.store.delete_by_id(event_id)
        if not ok:
            raise NotFoundError(f"Event with id {event_id} not found")


    # -------- helper methods below --------
    # edit event still needs to be implemented

    def _new_event_id(self) -> str:
        '''
        Generate a new event id.

        Returns:
            str: A new event id.
        '''
        # short memorable id like evt-7d3f
        return f"evt-{token_hex(2)}"  # 4 hex chars

    def _parse_date(self, s: str) -> date:
        '''
        Parse a date string and return a date object.

        Args:
            s: The date string to parse.

        Returns:
            date: A date object.
        '''
        s = (s or "").strip()
        try:
            # expects YYYY-MM-DD
            return date.fromisoformat(s)
        except ValueError:
            raise InvalidInputError(f'Invalid date format "{s}" (expected YYYY-MM-DD)')

    def _normalize_time(self, s: str) -> str:
        '''
        Normalize a time string and return a normalized time string.

        Args:
            s: The time string to normalize.

        Returns:
            str: A normalized time string.
        '''
        s = (s or "").strip()
        try:
            dt = datetime.strptime(s, "%H:%M")
            # normalize to zero-padded HH:MM
            return dt.strftime("%H:%M")
        except ValueError:
            raise InvalidInputError(f'Invalid time format "{s}" (expected HH:MM 24-hour)')

    def _validate_duration(self, duration: int) -> int:
        '''
        Validate a duration and return a validated duration.

        Args:
            duration: The duration to validate.

        Returns:
            int: A validated duration.
        '''
        # argparse type=int already gives int, but still validate range
        if duration is None:
            raise InvalidInputError("Duration is required")
        if duration <= 0:
            raise InvalidInputError("Duration must be a positive integer (minutes)")
        if duration > 24 * 60:
            raise InvalidInputError("Duration is too large")
        return duration