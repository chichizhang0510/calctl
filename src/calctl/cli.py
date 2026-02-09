'''
CLI for calctl

This module provides the command-line interface for the calctl application.
It handles command parsing, argument validation, and service invocation.
Special error handling is included for CLI-specific errors.
'''

import argparse
import sys
import json
from typing import Any
from pathlib import Path
from datetime import date

from .models import Event
from .color import Color
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
    examples = """Examples:
    calctl add --title "Meeting" --date 2024-03-15 --time 14:00 --duration 60
    calctl add --title "Standup" --date 2024-03-15 --time 10:00 --duration 30 --repeat weekly --count 4
    calctl list --today
    calctl agenda --week
    calctl search "meeting"
    calctl delete evt-8a2f --dry-run
    """

    p = argparse.ArgumentParser(
        prog="calctl",
        description="calctl - A command-line calendar manager",
        epilog=examples,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("-v", "--version", action="version", version="calctl 0.1.0")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")

    fmt = p.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="Output in JSON format")
    fmt.add_argument("--plain", action="store_true", help="Output in plain text (default)")

    sub = p.add_subparsers(dest="cmd")

    add = sub.add_parser("add", help="Add a new event")
    add.add_argument("--title", required=True)
    add.add_argument("--date", required=True)
    add.add_argument("--time", required=True)
    add.add_argument("--duration", required=True, type=int)
    add.add_argument("--description")
    add.add_argument("--location")
    add.add_argument("--force", action="store_true", help="Skip conflict checks")
    add.add_argument("--repeat", choices=["daily", "weekly"], help="Create recurring events")
    add.add_argument("--count", type=int, default=1, help="Number of occurrences (used with --repeat)")


    listp = sub.add_parser("list", help="List events")
    # mutually exclusive: --today vs --week vs --from/--to（range）
    g = listp.add_mutually_exclusive_group()
    g.add_argument("--today", action="store_true", help="List today's events")
    g.add_argument("--week", action="store_true", help="List events this week (Sun-Sat)")
    listp.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    listp.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")

    show = sub.add_parser("show", help="Show event details")
    show.add_argument("id")

    deletep = sub.add_parser("delete", help="Delete event(s)")
    target = deletep.add_mutually_exclusive_group(required=True)
    target.add_argument("id", nargs="?", help="Event id to delete (e.g., evt-8a2f)")
    target.add_argument("--date", dest="date", help="Delete all events on date (YYYY-MM-DD)")
    deletep.add_argument("--force", action="store_true", help="Skip confirmation")
    deletep.add_argument("--dry-run", action="store_true", help="Show what would be deleted")

    editp = sub.add_parser("edit", help="Edit an existing event")
    editp.add_argument("id", help="Event id (e.g., evt-8a2f)")
    editp.add_argument("--title")
    editp.add_argument("--description")
    editp.add_argument("--date")
    editp.add_argument("--time")
    editp.add_argument("--duration", type=int)
    editp.add_argument("--location")

    searchp = sub.add_parser("search", help="Search events by title/description/etc.")
    searchp.add_argument("query", help="Search phrase (case-insensitive, partial match)")
    searchp.add_argument("--title", action="store_true", help="Search only in titles")

    agp = sub.add_parser("agenda", help="Show agenda view (today, week, or a specific date)")
    mx = agp.add_mutually_exclusive_group()
    mx.add_argument("--week", action="store_true", help="Show this week's agenda (Sun-Sat)")
    mx.add_argument("--date", help="Show agenda for a specific date (YYYY-MM-DD)")

    return p

def event_to_dict(e: Event) -> dict[str, Any]:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "date": e.date.isoformat(),
        "start_time": e.start_time,
        "duration_min": e.duration_min,
        "location": e.location,
        "created_at": e.create_at.isoformat(),
        "updated_at": e.update_at.isoformat(),
    }

def events_to_json(events: list[Event]) -> str:
    return json.dumps([event_to_dict(e) for e in events], indent=2, ensure_ascii=False)

def _format_search_table(events: list[Event]) -> str:
    # required columns: id / date / time / duration / title
    rows = []
    for e in events:
        rows.append([
            e.id,
            e.date.isoformat(),
            e.start_time,
            str(e.duration_min),
            e.title,
        ])

    headers = ["ID", "Date", "Time", "Duration", "Title"]
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(r: list[str]) -> str:
        return "  ".join(r[i].ljust(widths[i]) for i in range(len(r)))

    out = []
    out.append(fmt_row(headers))
    out.append("  ".join("-" * w for w in widths))
    for r in rows:
        out.append(fmt_row(r))
    return "\n".join(out)

def _format_day_agenda(d: date, events: list[Event]) -> str:
    out = []
    out.append(f"{d.isoformat()} - Agenda")
    out.append(f"Total: {len(events)} event(s)")
    out.append("-" * 60)
    if not events:
        out.append("Free")
        return "\n".join(out)

    for e in events:
        out.append(f'{e.start_time} -> {e.end_dt().strftime("%H:%M")}  {e.title}')
    return "\n".join(out)

def _format_week_agenda(week: dict[date, list[Event]]) -> str:
    dates = sorted(week.keys())
    week_start = dates[0]
    week_end = dates[-1]
    out = []
    out.append(f"Week Agenda ({week_start.isoformat()} ~ {week_end.isoformat()})")
    out.append("=" * 60)

    total = sum(len(v) for v in week.values())
    out.append(f"Total: {total} event(s)\n")

    for d in dates:
        evs = week[d]
        out.append(f"{d.isoformat()} ({len(evs)} event(s))")
        if not evs:
            out.append("  Free")
        else:
            for e in evs:
                out.append(f'  {e.start_time}->{e.end_dt().strftime("%H:%M")}  {e.title}')
        out.append("")  # blank line
    return "\n".join(out)

def main() -> None:
    '''
    Main function for the command-line interface.

    Returns:
        None
    '''
    parser = build_parser()
    args = parser.parse_args()

    use_color = not args.no_color
    c_out = Color(use_color, stream="stdout")
    c_err = Color(use_color, stream="stderr")

    if args.cmd is None:
        parser.print_help()
        raise SystemExit(0)
    
    store = JsonEventStore(default_data_path())
    svc = CalendarService(store)

    try:
        if args.cmd == "add":
            created = svc.add_event(
                args.title, args.date, args.time, args.duration,
                args.description, args.location,
                force=args.force,
                repeat=args.repeat,
                count=args.count,
            )

            if args.json:
                print(json.dumps([event_to_dict(e) for e in created], indent=2, ensure_ascii=False))
            else:
                if len(created) == 1:
                    print(c_out.green(f"Event {created[0].id} created successfully"))
                else:
                    print(c_out.green(f"Recurring events created ({len(created)} occurrences):"))
                    for e in created:
                        print(f"- {e.id} {e.date.isoformat()} {e.start_time}-{e.end_dt().strftime('%H:%M')} {e.title}")
        elif args.cmd == "list":
            from_d = svc.parse_date(args.from_date) if getattr(args, "from_date", None) else None
            to_d = svc.parse_date(args.to_date) if getattr(args, "to_date", None) else None
            if getattr(args, "today", False):
                events = svc.list_events(today_only=True)
            elif getattr(args, "week", False):
                events = svc.list_events(week=True)
            elif args.from_date or args.to_date:
                from_d = svc.parse_date(args.from_date) if args.from_date else None
                to_d = svc.parse_date(args.to_date) if args.to_date else None
                events = svc.list_events(from_date=from_d, to_date=to_d)
            
            else:
                from_d = date.today()
                events = svc.list_events(from_date=from_d, to_date=None)
            
            if args.json:
                print(events_to_json(events)) 
            else:
                if not events:
                    print(c_out.yellow("No events found."))
                else:
                    # 打印表头
                    print(f"{'ID':<12} {'Date':<12} {'Time':<8} {'Duration':<10} {'Title'}")
                    print("-" * 70)
                    # 打印事件
                    for e in events:
                        duration_str = f"{e.duration_min} min"
                        print(f"{e.id:<12} {e.date.isoformat():<12} {e.start_time:<8} {duration_str:<10} {e.title}")
        elif args.cmd == "show":
            e, conflicts = svc.show_event_with_conflicts(args.id)
            if args.json:
                obj = {
                    "event": event_to_dict(e),
                    "conflicts": [event_to_dict(c) for c in conflicts],
                }
                print(json.dumps(obj, indent=2, ensure_ascii=False))
            else:
                print(f"ID: {e.id}")
                print(f"Title: {e.title}")
                print(f"Description: {e.description or '-'}")
                print(f"Date: {e.date.isoformat()}")
                print(f"Start: {e.start_time}")
                print(f"End: {e.end_dt().strftime('%H:%M')}")
                print(f"Duration: {e.duration_min} min")
                print(f"Location: {e.location or '-'}")
                print(f"Created: {e.create_at.isoformat()}")
                print(f"Updated: {e.update_at.isoformat()}")

                if conflicts:
                    print(c_out.yellow("\nConflicts:"))
                    for c in conflicts:
                        print(f'- {c.id} "{c.title}" ({c.start_time}-{c.end_dt().strftime("%H:%M")})')
                else:
                    print(c_out.green("\nConflicts: none"))
        elif args.cmd == "search":
            results = svc.search_events(args.query, title_only=args.title)

            if args.json:
                print(json.dumps([event_to_dict(e) for e in results], indent=2, ensure_ascii=False))
            else:
                if not results:
                    print(c_out.yellow(f'Found 0 events matching "{args.query}"'))
                else:
                    print(c_out.yellow(f'Found {len(results)} event(s) matching "{args.query}":'))
                    print(_format_search_table(results))
        elif args.cmd == "delete":
            if args.date:
                # delete by date
                to_delete = svc.get_events_on_date(args.date)  # list[Event]

                if not to_delete:
                    if args.json:
                        print(json.dumps({"date": args.date, "deleted_count": 0, "deleted": []}))
                    else:
                        print(c_out.yellow("No events to delete."))
                    sys.exit(0)

                if args.dry_run:
                    if args.json:
                        print(json.dumps({
                            "action": "dry-run",
                            "date": args.date,
                            "targets": [event_to_dict(e) for e in to_delete]
                        }, indent=2))
                    else:
                        print(c_out.yellow(f"Would delete {len(to_delete)} event(s) on {args.date}:"))
                        for e in to_delete:
                            print(f'- {e.id} {e.start_time}-{e.end_dt().strftime("%H:%M")} {e.title}')
                    sys.exit(0)

                if not args.force and not args.json:
                    print(c_out.yellow(f'About to delete {len(to_delete)} event(s) on {args.date}:'))
                    for e in to_delete:
                        print(f'- {e.id} {e.start_time}-{e.end_dt().strftime("%H:%M")} {e.title}')
                    ans = input("Proceed? [y/N]: ").strip().lower()
                    if ans not in ("y", "yes"):
                        print(c_err.red("Aborted."), file=sys.stderr)
                        sys.exit(1)

                deleted_events = to_delete
                deleted_count = svc.delete_on_date(args.date)
                
                if args.json:
                    print(json.dumps({
                        "date": args.date,
                        "deleted_count": deleted_count,
                        "deleted": [event_to_dict(e) for e in deleted_events]
                    }, indent=2))
                else:
                    print(c_out.green(f"Deleted {deleted_count} event(s)."))

            else:
                # delete by id
                e = svc.show_event(args.id)

                if args.dry_run:
                    if args.json:
                        print(json.dumps({
                            "action": "dry-run",
                            "targets": [event_to_dict(e)]
                        }, indent=2))
                    else:
                        print(c_out.yellow(f'Would delete: {e.id} {e.date.isoformat()} {e.start_time}-{e.end_dt().strftime("%H:%M")} {e.title}'))
                    sys.exit(0)

                if not args.force and not args.json:
                    print(c_out.yellow("About to delete:"))
                    print(f'  {e.id} {e.date.isoformat()} {e.start_time}-{e.end_dt().strftime("%H:%M")} {e.title}')
                    ans = input("Proceed? [y/N]: ").strip().lower()
                    if ans not in ("y", "yes"):
                        print(c_err.red("Aborted."), file=sys.stderr)
                        sys.exit(1)

                deleted_event = svc.delete_event(args.id)
                if args.json:
                    print(json.dumps({
                        "deleted": [event_to_dict(deleted_event)]
                    }, indent=2))
                else:
                    print(c_out.green(f"Deleted: {deleted_event.id}"))
        elif args.cmd == "edit":
            e, changes = svc.edit_event(
                args.id,
                title=args.title,
                description=args.description,
                date_str=args.date,
                time_str=args.time,
                duration=args.duration,
                location=args.location,
            )

            if args.json:
                obj = {
                    "event": event_to_dict(e),
                    "changes": {k: {"from": v[0], "to": v[1]} for k, v in changes.items()},
                }
                print(json.dumps(obj, indent=2, ensure_ascii=False))
            else:
                print(c_out.green(f"Updated: {e.id}"))
                if not changes:
                    print(c_out.yellow("No changes."))
                else:
                    print(c_out.bold("Changes:"))
                    for k, (before, after) in changes.items():
                        print(f"- {k}: {before} -> {after}")
        elif args.cmd == "agenda":
            if args.week:
                week = svc.agenda_week()
                if args.json:
                    obj = {d.isoformat(): [event_to_dict(e) for e in evs] for d, evs in week.items()}
                    print(json.dumps(obj, indent=2, ensure_ascii=False))
                else:
                    print(_format_week_agenda(week))
            else:
                d = svc.parse_date_public(args.date) if args.date else date.today()
                day_events = svc.agenda_day(d)
                if args.json:
                    print(json.dumps([event_to_dict(e) for e in day_events], indent=2, ensure_ascii=False))
                else:
                    print(_format_day_agenda(d, day_events))
        else:
            build_parser().print_help()
            sys.exit(0)
    except KeyboardInterrupt:
        print(c_err.red("\nCancelled."), file=sys.stderr)
        raise SystemExit(130)
    except CalctlError as ex:
        print(c_err.red(f"Error: {ex}"), file=sys.stderr)
        sys.exit(ex.exit_code)