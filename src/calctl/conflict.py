'''
Conflict detection for calendar events.

This module provides functions to detect conflicts between calendar events.
'''

from __future__ import annotations  # for type hints

from .models import Event


def overlaps(a: Event, b: Event) -> bool:
    '''
    Check if two events overlap.

    Args:
        a: The first event.
        b: The second event.
    '''
    # same event id should not compare
    if a.id == b.id:
        return False
    # only compare if on same date (your model is date-based)
    if a.date != b.date:
        return False
    # interval overlap: [start, end)
    return a.start_dt() < b.end_dt() and b.start_dt() < a.end_dt()
