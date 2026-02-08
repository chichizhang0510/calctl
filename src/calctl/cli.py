'''
CLI for calctl

This module provides the command-line interface for the calctl application.
It handles command parsing, argument validation, and service invocation.
Special error handling is included for CLI-specific errors.
'''

import argparse
import sys
from pathlib import Path
from .service import CalendarService
from .store import JsonEventStore
from .errors import InvalidInputError, NotFoundError, StorageError, CalctlError

def default_data_path() -> Path:
    '''
    Return the default data path for the event store.

    Returns:
        Path: The default data path for the event store.
    '''
    return Path.home() / ".calctl" / "events.json"

def build_parser() -> argparse.ArgumentParser:
    '''
    Build the argument parser for the command-line interface.

    Returns:
        argparse.ArgumentParser: The argument parser for the command-line interface.
    '''
    p = argparse.ArgumentParser(prog="calctl", description="calctl - A command-line calendar manager")
    sub = p.add_subparsers(dest="cmd")

    add = sub.add_parser("add", help="Add a new event")
    add.add_argument("--title", required=True)
    add.add_argument("--date", required=True)
    add.add_argument("--time", required=True)
    add.add_argument("--duration", required=True, type=int)
    add.add_argument("--description")
    add.add_argument("--location")

    sub.add_parser("list", help="List events")

    show = sub.add_parser("show", help="Show event details")
    show.add_argument("id")

    delete = sub.add_parser("delete", help="Delete event(s)")
    delete.add_argument("id")

    return p


def main() -> None:
    '''
    Main function for the command-line interface.

    Returns:
        None
    '''
    args = build_parser().parse_args()

    store = JsonEventStore(default_data_path())
    svc = CalendarService(store)

    try:
        if args.cmd == "add":
            e = svc.add_event(args.title, args.date, args.time, args.duration, args.description, args.location)
            print(f'Event {e.id} created successfully')
        elif args.cmd == "list":
            events = svc.list_events()
            for e in events:
                print(e.id, e.date, e.start_time, e.duration_min, e.title)
        elif args.cmd == "show":
            e = svc.show_event(args.id)
            print(e)
        elif args.cmd == "delete":
            svc.delete_event(args.id)
            print("Deleted")
        else:
            build_parser().print_help()
            sys.exit(0)
    except CalctlError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(ex.exit_code)