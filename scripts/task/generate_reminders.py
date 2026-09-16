"""Read repository tasks and produce a single dated reminder message."""

from __future__ import annotations

import argparse
import calendar
import json
from datetime import date, datetime, timezone
from pathlib import Path


def one_month_after(day: date) -> date:
    """Return the same day next month, clamped to that month's last day."""
    year = day.year + (day.month == 12)
    month = day.month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def read_active_tasks(path: Path) -> list[tuple[date, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise ValueError("Task data must contain a 'tasks' list")

    active = []
    ids = set()
    for index, item in enumerate(data["tasks"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Task {index} must be an object")
        for field in ("id", "task", "date", "status"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Task {index} needs a nonempty string '{field}'")
        if item["id"] in ids:
            raise ValueError(f"Duplicate task id: {item['id']}")
        ids.add(item["id"])
        due = date.fromisoformat(item["date"])
        if due.isoformat() != item["date"]:
            raise ValueError(f"Task {index} date must use YYYY-MM-DD")
        if item["status"] == "active":
            name = " ".join(item["task"].split())
            active.append((due, name))
    return sorted(active, key=lambda task: (task[0], task[1]))


def format_remaining(days: int, upcoming: bool = False) -> str:
    if days < 0:
        count = -days
        return f"overdue by {count} day{'s' if count != 1 else ''}"
    if days == 0:
        return "due today"
    if upcoming:
        months = max(1, round(days / 30.44))
        return f"{months} month{'s' if months != 1 else ''} left"
    return f"{days} day{'s' if days != 1 else ''} left"


def render_message(sections: dict[str, list[str]], omitted_upcoming: int = 0) -> str:
    blocks = ["📋 Task Status"]
    for heading, lines in sections.items():
        if not lines and not (heading == "⏲ Upcoming Tasks" and omitted_upcoming):
            continue
        body = "\n".join(lines)
        if heading == "⏲ Upcoming Tasks" and omitted_upcoming:
            note = f"… {omitted_upcoming} upcoming task{'s' if omitted_upcoming != 1 else ''} omitted"
            body = f"{body}\n{note}" if body else note
        blocks.append(f"{heading}\n\n{body}")
    if len(blocks) == 1:
        blocks.append("No active tasks.")
    return "\n\n".join(blocks)


def generate_message(
    tasks: list[tuple[date, str]], today: date, max_characters: int | None = None
) -> str:
    if max_characters is not None and max_characters <= 0:
        raise ValueError("max_characters must be positive")
    sections: dict[str, list[str]] = {
        "🆘 Urgent Tasks": [],
        "⚠️ Beware Tasks": [],
        "⏲ Upcoming Tasks": [],
    }
    month_limit = one_month_after(today)
    for due, name in sorted(tasks, key=lambda task: (task[0], task[1])):
        days = (due - today).days
        if days <= 7:
            heading = "🆘 Urgent Tasks"
        elif due <= month_limit:
            heading = "⚠️ Beware Tasks"
        else:
            heading = "⏲ Upcoming Tasks"
        number = len(sections[heading]) + 1
        remaining = format_remaining(days, upcoming=heading == "⏲ Upcoming Tasks")
        sections[heading].append(f"{number}. {name} — {remaining} — {due.isoformat()}")

    omitted_upcoming = 0
    message = render_message(sections)
    while max_characters is not None and len(message) > max_characters:
        if not sections["⏲ Upcoming Tasks"]:
            raise ValueError("Report exceeds the message limit after omitting all Upcoming tasks")
        sections["⏲ Upcoming Tasks"].pop()
        omitted_upcoming += 1
        message = render_message(sections, omitted_upcoming)
    return message


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=Path("data/task/tasks.json"))
    parser.add_argument("--today", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument("--max-characters", type=int, help="Omit farthest upcoming tasks to fit this limit")
    parser.add_argument("--output", type=Path, help="Write the message to a file instead of stdout")
    args = parser.parse_args()
    try:
        message = generate_message(read_active_tasks(args.tasks), args.today, args.max_characters)
    except ValueError as exc:
        parser.error(str(exc))
    if args.output:
        args.output.write_text(message + "\n", encoding="utf-8")
    else:
        print(message)


if __name__ == "__main__":
    main()
