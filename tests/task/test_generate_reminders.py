import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.task.generate_reminders import generate_message, read_active_tasks


class ReminderTests(unittest.TestCase):
    def test_filters_sorts_and_labels_boundary_dates(self):
        entries = [
            {"id": "upcoming", "task": "Conference", "date": "2026-10-17", "status": "active"},
            {"id": "inactive", "task": "Ignore me", "date": "2026-09-17", "status": "done"},
            {"id": "beware", "task": "Launch", "date": "2026-10-16", "status": "active"},
            {"id": "urgent", "task": "Review", "date": "2026-09-23", "status": "active"},
            {"id": "overdue", "task": "Submission", "date": "2026-09-15", "status": "active"},
            {"id": "after-urgent", "task": "Docs", "date": "2026-09-24", "status": "active"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            path.write_text(json.dumps({"tasks": entries}), encoding="utf-8")
            message = generate_message(read_active_tasks(path), date(2026, 9, 16))

        self.assertNotIn("Ignore me", message)
        self.assertIn("1. Submission — overdue by 1 day — 2026-09-15", message)
        self.assertIn("2. Review — 7 days left — 2026-09-23", message)
        self.assertIn("1. Docs — 8 days left — 2026-09-24", message)
        self.assertIn("2. Launch — 30 days left — 2026-10-16", message)
        self.assertIn("1. Conference — 1 month left — 2026-10-17", message)
        self.assertLess(message.index("🆘 Urgent Tasks"), message.index("⚠️ Beware Tasks"))
        self.assertLess(message.index("⚠️ Beware Tasks"), message.index("⏲ Upcoming Tasks"))

    def test_month_boundary_clamps_at_end_of_february(self):
        tasks = [(date(2026, 2, 28), "February close"), (date(2026, 3, 1), "March start")]
        message = generate_message(tasks, date(2026, 1, 31))
        self.assertIn("⚠️ Beware Tasks\n\n1. February close", message)
        self.assertIn("⏲ Upcoming Tasks\n\n1. March start", message)

    def test_empty_active_tasks_has_clear_report(self):
        self.assertEqual(generate_message([], date(2026, 9, 16)), "📋 Task Status\n\nNo active tasks.")


if __name__ == "__main__":
    unittest.main()
