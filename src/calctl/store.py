'''
Event store implementation using JSON files.

This module provides a persistent storage for calendar events using JSON files.
It handles the serialization and deserialization of event data to and from JSON.
'''

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any
from datetime import datetime,date

from .errors import StorageError
from .models import Event


class JsonEventStore:
    def __init__(self, path: Path):
        self.path = path

    def list_all(self) -> list[Event]:
        '''
        List all events in the store.

        Returns:
            list[Event]: A list of all events in the store.
        '''
        data = self._load_data()
        events = [self._event_from_dict(e) for e in data["events"]]
        events.sort(key=lambda e: (e.date.isoformat(), e.start_time, e.id))
        return events
    
    def get_by_id(self, event_id: str) -> Event | None: 
        '''
        Get an event by its id.

        Args:
            event_id: The id of the event.

        Returns:
            Event | None: The event or None if not found.
        '''
        for e in self._load_data()["events"]:
            if e["id"] == event_id:
                return self._event_from_dict(e)
        return None
    
    def add(self, event:Event) -> None:
        '''
        Add an event to the store.

        Args:
            event: The event to add.
        '''
        data = self._load_data()
        if any(e["id"] == event.id for e in data["events"]):
            raise StorageError(f"Event with id {event.id} already exists")
        data["events"].append(self._event_to_dict(event))
        self._save_data(data)

    def update(self, event:Event) -> None:  
        '''
        Update an event in the store.

        Args:
            event: The event to update.
        '''
        data = self._load_data()
        for i, e in enumerate(data["events"]):
            if e["id"] == event.id:
                data["events"][i] = self._event_to_dict(event)
                self._save_data(data)
                return
        raise StorageError(f"Event with id {event.id} not found")

    def delete_by_id(self, event_id: str) -> bool:
        '''
        Delete an event by its id.

        Args:
            event_id: The id of the event.

        Returns:
            bool: True if the event was deleted, False otherwise.
        '''
        data = self._load_data()
        for i, e in enumerate(data["events"]):
            if e["id"] == event_id:
                del data["events"][i]
                self._save_data(data)
                return True
        return False
    
    def delete_by_date(self, date_str: str) -> int:
        '''
        Delete events by date.

        Args:
            date: The date of the events.

        Returns:
            int: The number of events deleted.
        '''
        try :
            target = date.fromisoformat(date_str.strip())
        except ValueError:
            raise InvalidInputError(f"Invalid date format: {date_str}")
        
        data = self._load_data()
        before = len(data["events"])
        data["events"] = [e for e in data["events"] if e["date"] != target.isoformat()]
        deletd = before - len(data["events"])
        if deleted > 0:
            self._save_data(data)
        return deleted
    

    # ---------- internal helpers ----------

    def _ensure_file(self) -> None:
        '''
        Ensure the file exists.

        Returns:
            None
        '''
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.path.write_text(json.dumps({"events": []}, indent=2), encoding="utf-8")
        except Exception as e:
            raise StorageError(f"Failed to ensure file exists: {e}")

    def _load_data(self) -> list[dict[str, Any]]:
        '''
        Load the data from the file.

        Returns:
            list[dict[str, Any]]: The data from the file.
        '''
        self._ensure_file()
        try:
            raw = self.path.read_text(encoding="utf-8")
            if not raw:
                return {"events": []}
            
            data = json.loads(raw)
            if isinstance(data, list):
                return {"events": data}
            if isinstance(data, dict) and "events" in data:
                return data
            raise StorageError(f"Invalid data format: {data}")
        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to parse JSON: {e}")
        except OSError as e:
            raise StorageError(f"Failed to read file: {e}")
    
    def _save_data(self, data: list[dict[str, Any]]) -> None:
        '''
        Save the data to the file.

        Args:
            data: The data to save.
        '''
        self._ensure_file()
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            content = json.dumps(data, indent=2)
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(self.path)
        except OSError as e:
            raise StorageError(f"Failed to write file: {e}")
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError as e:
                raise StorageError(f"Failed to delete temporary file: {e}")
    
    def _event_to_dict(self, event: Event) -> dict[str, Any]:
        '''
        Convert an event to a dictionary.

        Args:
            event: The event to convert.
        '''
        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.isoformat(),
            "start_time": event.start_time,
            "duration_min": event.duration_min,
            "location": event.location,
            "create_at": event.create_at.isoformat(),
            "update_at": event.update_at.isoformat(),
        }
    
    def _event_from_dict(self, data: dict[str, Any]) -> Event:
        '''
        Convert a dictionary to an event.

        Args:
            data: The dictionary to convert.
        '''
        try:
            return Event(
                id=str(data["id"]),
                title=str(data["title"]),
                description=data["description"],
                date=date.fromisoformat(data["date"]),
                start_time=str(data["start_time"]),
                duration_min=int(data["duration_min"]),
                location=data.get("location"),
                create_at=datetime.fromisoformat(data["create_at"]),
                update_at=datetime.fromisoformat(data["update_at"]),
            )
        except KeyError as e:
            raise StorageError(f"Missing required field: {e}")
