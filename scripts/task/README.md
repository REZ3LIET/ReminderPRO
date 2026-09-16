# Task reminders

The [task reminder workflow](../../.github/workflows/task-reminders.yml) runs daily at 09:17 UTC and supports manual runs from GitHub Actions. It reads [task data](../../data/task/tasks.json), runs [the Python generator](generate_reminders.py), and sends the resulting report through a provider-specific Actions step. Python only processes tasks and writes the message. The workflow never adds, edits, archives, or deletes tasks.

The task file is JSON with a top-level `tasks` array. Each task needs a unique string `id`, a nonempty `task` name, an ISO due `date` (`YYYY-MM-DD`), and a string `status`. Only entries whose status is exactly `active` appear in the report. Edit the JSON file to manage tasks; the reminder workflow only reads it.

The generator uses the current UTC date unless `--today` is supplied. It sorts active tasks by due date, then groups them as follows:

| Category | Due date | Remaining-time label |
| --- | --- | --- |
| 🆘 Urgent | In 7 days or less, including past due | Days left, due today, or overdue by days |
| ⚠️ Beware | After 7 days and no later than one calendar month from today | Days left |
| ⏲ Upcoming | Later than one calendar month from today | Approximate months left |

The one-month boundary uses the same day next month, clamped to that month's last day; for example, January 31 maps to February 28 in a non-leap year. Upcoming months are rounded from days divided by 30.44. The report omits empty categories and says `No active tasks.` if none qualify. Each listed task includes its name, remaining-time label, and ISO due date.

To preview the report from the repository root without sending it:

```sh
python3 scripts/task/generate_reminders.py --today 2026-09-16
```

Omit `--today` to use today's UTC date. `--tasks` selects another JSON file, and `--output report.txt` writes the message to a file instead of stdout. Run the task tests with `python3 -m unittest discover -s tests -v`.

## Delivery configuration

Set the repository Actions variable `TASK_REMINDERS_PROVIDER` to `discord` (the default) or `slack`. Add the matching repository secret `TASK_REMINDERS_DISCORD_WEBHOOK_URL` or `TASK_REMINDERS_SLACK_WEBHOOK_URL`. The destination channel comes from the webhook you create in Discord or Slack. Set the optional `TASK_REMINDERS_DATA_PATH` variable to use a different JSON task file. The older generic names `NOTIFICATION_PROVIDER`, `TASK_DATA_PATH`, `DISCORD_WEBHOOK_URL`, and `SLACK_WEBHOOK_URL` remain supported as fallbacks.

Edit `schedule.cron` in the workflow to change its run time. GitHub Actions reads the generated message file, builds the selected provider's JSON payload with `jq`, and posts it with `curl`. The Discord step rejects a report over 2,000 characters. A missing provider secret or unsupported provider setting fails the workflow with a clear error. No webhook URL belongs in the repository.
