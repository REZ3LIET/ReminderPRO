# ReminderPRO
Sends reminder to preferred app, PRO stands for Primarily Redundant Opportunity

## Scheduled task reminders

Each scheduled job has its own matching folders for data, Python code, and tests. GitHub requires workflows to stay in `.github/workflows/`, so each workflow is named for its job:

```text
.github/workflows/task-reminders.yml
data/task_reminders/tasks.json
scripts/task_reminders/generate_reminders.py
scripts/task_reminders/send_notification.py
tests/task_reminders/
```

Add another scheduled job as `data/<job_name>/`, `scripts/<job_name>/`, `tests/<job_name>/`, and `.github/workflows/<job-name>.yml`. Use that job's name to prefix its GitHub Actions variables and secrets, so each job can have its own data source and notification destination.

The [task reminder workflow](.github/workflows/task-reminders.yml) runs every day at 09:17 UTC and can also be started from the GitHub Actions tab with **Run workflow**. It reads [task data](data/task_reminders/tasks.json), generates one report, and posts it to a Discord or Slack incoming webhook. It never edits task data.

Edit the workflow's `schedule.cron` to choose a different time. In **Settings → Secrets and variables → Actions**, set `TASK_REMINDERS_PROVIDER` to `discord` (the default) or `slack`, and add the matching secret `TASK_REMINDERS_DISCORD_WEBHOOK_URL` or `TASK_REMINDERS_SLACK_WEBHOOK_URL`. Set the optional `TASK_REMINDERS_DATA_PATH` variable to point to another JSON task file. The earlier generic variable names (`NOTIFICATION_PROVIDER`, `TASK_DATA_PATH`) and webhook secrets still work as fallbacks. The destination channel is determined by the webhook you create in Discord or Slack; no URL belongs in this repository. The job fails clearly if its selected webhook secret is missing.

The task file contains a top-level `tasks` array. Each entry needs a unique string `id`, a `task` name, an ISO `date` (`YYYY-MM-DD`), and a string `status`. Only entries with `"status": "active"` appear in the report. Edit the task file to manage tasks; this workflow only reads it.

The [Python generator](scripts/task_reminders/generate_reminders.py) uses the current UTC date. Deadlines up to seven days away, including overdue deadlines, are urgent. Deadlines after seven days but no later than the same calendar day next month are beware tasks. Later deadlines are upcoming tasks, with months rounded from the number of days divided by 30.44. For dates such as January 31, the one-month boundary is clamped to the last day of February. Empty categories are omitted, and a report with no active tasks says so. Discord limits webhook message content to 2,000 characters; the sender fails with a clear error if the report exceeds that limit.

To preview a report without sending it, run:

```sh
python3 scripts/task_reminders/generate_reminders.py --tasks data/task_reminders/tasks.json --today 2026-09-16
```

Omit `--today` to use the current UTC date. You can use `--output report.txt` to capture the message in a file. The sender reads that file and uses the selected webhook URL from its environment. Neither script needs third-party packages or a virtual environment.
