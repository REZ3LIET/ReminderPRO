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

The generator accepts `--max-characters` for destinations with a message limit. If a report exceeds that limit, it removes the farthest Upcoming tasks first and states how many were omitted. It always keeps Urgent and Beware tasks; if those and the omission note cannot fit, generation fails rather than silently dropping them. The workflow passes the 2,000-character limit for Discord. Slack uses the full report.

To preview the report from the repository root without sending it:

```sh
python3 scripts/task/generate_reminders.py --today 2026-09-16
```

Omit `--today` to use today's UTC date. `--tasks` selects another JSON file, and `--output report.txt` writes the message to a file instead of stdout. Add `--max-characters 2000` to preview the Discord-sized report. Run the task tests with `python3 -m unittest discover -s tests -v`.

## GitHub Actions setup

Create an **incoming webhook** in the Discord or Slack channel that should receive reports, then copy its full URL. Configure these settings in the GitHub repository under **Settings → Secrets and variables → Actions** ([secrets guide](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets), [variables guide](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-variables)):

| Name | GitHub setting | When needed | Value |
| --- | --- | --- | --- |
| `TASK_REMINDERS_PROVIDER` | Variable | Optional | `discord` or `slack`; defaults to `discord` |
| `TASK_REMINDERS_DATA_PATH` | Variable | Optional | Repository-relative JSON path; defaults to `data/task/tasks.json` |
| `TASK_REMINDERS_DISCORD_WEBHOOK_URL` | Secret | Required for Discord | Full Discord incoming webhook URL |
| `TASK_REMINDERS_SLACK_WEBHOOK_URL` | Secret | Required for Slack | Full Slack incoming webhook URL |

For Discord, the default provider already applies: create `TASK_REMINDERS_DISCORD_WEBHOOK_URL` under the **Secrets** tab using **New repository secret**. For Slack, create `TASK_REMINDERS_SLACK_WEBHOOK_URL` as a secret and add `TASK_REMINDERS_PROVIDER=slack` under the **Variables** tab using **New repository variable**. Set `TASK_REMINDERS_DATA_PATH` only if the task JSON lives somewhere else. The unused provider's secret is not required. Store webhook URLs only as secrets, never in JSON, an `.env` file, or the workflow source.

GitHub Actions turns these repository settings into temporary step environment variables. `REMINDER_PROVIDER` selects the delivery step, `TASK_DATA_PATH` tells the generator which JSON file to read, and `WEBHOOK_URL` is supplied only to the selected Discord or Slack delivery step. These three names and GitHub's built-in `RUNNER_TEMP` do **not** need to be created in repository Settings. Python receives the task path and message limit as command-line arguments; it never receives a webhook URL. No local environment variables or credentials are needed to preview a report or run its tests.

After the workflow is on the default branch, open **Actions → Task reminders → Run workflow** for a [manual delivery test](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow). This run posts to the configured channel. The scheduled run uses `17 9 * * *` (09:17 UTC each day); edit `schedule.cron` in the workflow to change it. GitHub Actions builds the provider's JSON payload with `jq` and posts it with `curl`. A missing selected secret or unsupported provider setting fails the workflow with a clear error. GitHub repository webhooks send repository events; this report uses a Discord or Slack incoming webhook so it can send the generated task text.
