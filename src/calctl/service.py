'''
Service layer for the calendar application.

This module contains the business logic for the calendar application.
It handles the interaction between the CLI and the data store.
'''

from dataclasses import replace
from datetime import date, datetime, timedelta
from secrets import token_hex

from .conflict import overlaps
from .errors import ConflictError, InvalidInputError, NotFoundError
from .models import Event
from .store import JsonEventStore


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
            location: str | None = None,
            *,
            force: bool = False,
            repeat: str | None = None,   # None | "daily" | "weekly"
            count: int = 1,
        ) -> list[Event]:
        '''
        Add a new event to the calendar.

        Args:
            title: The title of the event.
            date_str: The date of the event.
            time_str: The time of the event.
            duration: The duration of the event.
            description: The description of the event.
            location: The location of the event.
            force: Whether to force the event to be added.
            repeat: Whether to repeat the event.
            count: The number of times to repeat the event.

        Returns:
            list[Event]: A list of events.
        '''
        # parse and validate input arguments
        title = (title or "").strip()
        if not title:
            raise InvalidInputError("Title is required")

        d = self._parse_date(date_str)
        t = self._normalize_time(time_str)
        dur = self._validate_duration(duration)
        now = datetime.now()

        if repeat is None:
            count = 1
            step = timedelta(days=0)
        else:
            if count is None or count <= 0:
                raise InvalidInputError("--count must be a positive integer")
            if repeat not in ("daily", "weekly"):
                raise InvalidInputError('--repeat must be "daily" or "weekly"')
            step = timedelta(days=1) if repeat == "daily" else timedelta(weeks=1)

        new_events: list[Event] = []

        for i in range(count):
            di = d + (step * i)
            e = Event(
                id=self._new_event_id(),
                title=title,
                description=(description.strip() if description else None),
                date=di,
                start_time=t,
                duration_min=dur,
                location=(location.strip() if location else None),
                create_at=now,
                update_at=now,
            )


            if e.end_dt().date() != e.start_dt().date():
                raise InvalidInputError("Event cannot cross midnight (duration too long)")

            new_events.append(e)

        if not force:
            existing = self.store.list_all()

            conflicts: list[tuple[Event, Event]] = []
            for ne in new_events:
                for ex in existing:
                    if overlaps(ne, ex):
                        conflicts.append((ne, ex))

            if conflicts:
                lines = ["Event conflicts with existing events:"]
                for (ne, ex) in conflicts:
                    lines.append(
                        f'- New "{ne.title}" on {ne.date.isoformat()} '
                        f'({ne.start_time}-{ne.end_dt().strftime("%H:%M")}) '
                        f'conflicts with "{ex.title}" ({ex.start_time}-{ex.end_dt().strftime("%H:%M")})'
                    )
                lines.append("Use --force to schedule anyway.")
                raise ConflictError("\n".join(lines))

        self.store.add_many(new_events)
        return new_events

    def list_events(self,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
        today_only: bool = False,
        week: bool = False,) -> list[Event]:
        '''
        List events in the calendar.

        Args:
            from_date: The start date of the events.
            to_date: The end date of the events.
            today_only: Whether to only list events for today.
            week: Whether to list events for the current week.

        Returns:
            list[Event]: A list of events.
        '''
        events = self.store.list_all()
        today = date.today()

        if today_only:
            return [e for e in events if e.date == today]

        if week:
            # week starts on Sunday
            # Python weekday(): Mon=0 ... Sun=6
            days_since_sun = (today.weekday() + 1) % 7
            week_start = today - timedelta(days=days_since_sun)
            week_end = week_start + timedelta(days=6)
            return [e for e in events if week_start <= e.date <= week_end]

        if from_date is not None or to_date is not None:
            if from_date is None:
                from_date = date.min
            if to_date is None:
                to_date = date.max
            return [e for e in events if from_date <= e.date <= to_date]

        return [e for e in events if e.date >= today]

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

    def show_event_with_conflicts(self, event_id: str) -> tuple[Event, list[Event]]:
        e = self.show_event(event_id)
        all_events = self.store.list_all()
        conflicts = [x for x in all_events if overlaps(e, x)]
        conflicts.sort(key=lambda x: (x.date.isoformat(), x.start_time, x.id))
        return e, conflicts

    def delete_event(self, event_id: str) -> Event:
        '''
        Delete an event by its id.

        Args:
            event_id: The id of the event.

        Returns:
            Event
        '''
        e = self.store.get_by_id(event_id)
        if e is None:
            raise NotFoundError(f"Event {event_id} not found")

        ok = self.store.delete_by_id(event_id)
        if not ok:
            raise NotFoundError(f"Event {event_id} not found")

        return e

    def get_events_on_date(self, date_str: str) -> list[Event]:
        '''
        Get events on a date.

        Args:
            date_str: The date of the events.

        Returns:
            list[Event]: A list of events.
        '''
        d = self._parse_date(date_str)
        events = [e for e in self.store.list_all() if e.date == d]
        return events

    def delete_on_date(self, date_str: str) -> int:
        '''
        Delete events on a date.

        Args:
            date_str: The date of the events.

        Returns:
            int: The number of events deleted.
        '''
        d = self._parse_date(date_str)
        return self.store.delete_by_date(d.isoformat())

    def parse_date(self, s: str) -> date:
        """Public wrapper for date parsing"""
        return self._parse_date(s)

    def edit_event(
        self,
        event_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        date_str: str | None = None,
        time_str: str | None = None,
        duration: int | None = None,
        location: str | None = None,) -> tuple[Event, dict[str, tuple[object, object]]]:
        """
        Edit an event by its id.

        Args:
            event_id: The id of the event.
            title: The new title of the event.
            description: The new description of the event.
            date_str: The new date of the event.
            time_str: The new time of the event.
            duration: The new duration of the event.
            location: The new location of the event.

        Returns: (updated_event, changes)
        changes: { field: (old, new), ... }
        """
        old = self.show_event(event_id)  # raises NotFoundError if not exists

        # Must provide at least one field
        if all(v is None for v in [title, description, date_str, time_str, duration, location]):
            raise InvalidInputError("No fields provided to edit")

        # Normalize / parse inputs (only if provided)
        new_title = old.title if title is None else title.strip()
        if title is not None and not new_title:
            raise InvalidInputError("Title cannot be empty")

        new_desc = old.description if description is None else (description.strip() if description else None)
        new_loc = old.location if location is None else (location.strip() if location else None)

        new_date = old.date if date_str is None else self._parse_date(date_str)
        new_time = old.start_time if time_str is None else self._normalize_time(time_str)
        new_dur = old.duration_min if duration is None else self._validate_duration(duration)

        now = datetime.now()

        updated = replace(
            old,
            title=new_title,
            description=new_desc,
            date=new_date,
            start_time=new_time,
            duration_min=new_dur,
            location=new_loc,
            update_at=now,
        )

        # Optional: forbid crossing midnight for simplicity
        if updated.end_dt().date() != updated.start_dt().date():
            raise InvalidInputError("Event cannot cross midnight (duration too long)")

        # Conflict validation: updated event must not overlap with any other event
        all_events = self.store.list_all()
        conflicts = [e for e in all_events if overlaps(updated, e)]
        if conflicts:
            # Keep message actionable
            msg_lines = ["Edit would create conflicts with:"]
            for c in conflicts:
                msg_lines.append(f'- {c.id} "{c.title}" ({c.start_time}-{c.end_dt().strftime("%H:%M")})')
            raise ConflictError("\n".join(msg_lines))

        # Persist
        self.store.update(updated)

        # Build diff
        changes: dict[str, tuple[object, object]] = {}
        def add_change(field: str, before: object, after: object) -> None:
            if before != after:
                changes[field] = (before, after)

        add_change("title", old.title, updated.title)
        add_change("description", old.description, updated.description)
        add_change("date", old.date.isoformat(), updated.date.isoformat())
        add_change("start_time", old.start_time, updated.start_time)
        add_change("duration_min", old.duration_min, updated.duration_min)
        add_change("location", old.location, updated.location)

        return updated, changes

    def search_events(self, query: str, *, title_only: bool = False) -> list[Event]:
        q = (query or "").strip().lower()
        if not q:
            raise InvalidInputError("Search query cannot be empty")

        events = self.store.list_all()

        def haystack(e: Event) -> str:
            if title_only:
                return (e.title or "").lower()
            parts = [
                e.id,
                e.title or "",
                e.description or "",
                e.location or "",
                e.date.isoformat(),
                e.start_time,
                str(e.duration_min),
            ]
            return " ".join(parts).lower()

        matched = [e for e in events if q in haystack(e)]
        matched.sort(key=lambda e: (e.date.isoformat(), e.start_time, e.id))
        return matched

    def agenda_day(self, d: date) -> list[Event]:
        events = [e for e in self.store.list_all() if e.date == d]
        events.sort(key=lambda e: (e.start_time, e.id))
        return events

    def agenda_week(self, anchor: date | None = None) -> dict[date, list[Event]]:
        if anchor is None:
            anchor = date.today()

        # week starts Sunday
        days_since_sun = (anchor.weekday() + 1) % 7
        week_start = anchor - timedelta(days=days_since_sun)

        week: dict[date, list[Event]] = {}
        for i in range(7):
            d = week_start + timedelta(days=i)
            week[d] = self.agenda_day(d)
        return week

    def parse_date_public(self, s: str) -> date:
        return self._parse_date(s)

    # -------- helper methods below --------
    # edit event still needs to be implemented

    def _new_event_id(self) -> str:
        '''
        Generate a new event id.

        Returns:
            str: A new event id.
        '''
        # short memorable id like evt-7d3f
        return f"evt-{token_hex(4)}"  # 4 hex chars

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
            raise InvalidInputError(f'Invalid date format "{s}" (expected YYYY-MM-DD)') from None

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
            raise InvalidInputError(f'Invalid time format "{s}" (expected HH:MM 24-hour)') from None

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
