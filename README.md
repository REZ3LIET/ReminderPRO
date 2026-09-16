# ReminderPRO

ReminderPRO runs scheduled workflows for repository tasks. Task data, task-processing code, and delivery settings are kept separate.

## Scheduled workflows

| Workflow | What it does | Details |
| --- | --- | --- |
| [Task reminders](.github/workflows/task-reminders.yml) | Reads active tasks, groups them by deadline, and sends one status report to Discord or Slack. It does not change task data. | [Task README](scripts/task/README.md) |

## Repository layout

`data/<area>/` holds structured data shared by workflows in that area. `scripts/<area>/` holds Python processing code and an area-specific README. `tests/<area>/` holds its tests. Each scheduled job has a separately named workflow in `.github/workflows/` because that is where GitHub Actions loads workflows. The current task area uses `data/task/`, `scripts/task/`, and `tests/task/`.

## General setup

Enable GitHub Actions for the repository. Scheduled workflows run from their configured cron entries and can be started manually from the Actions tab. Store webhook URLs and other credentials in **Settings → Secrets and variables → Actions** as secrets; keep non-secret options there as variables. Each workflow sets up its own runtime and names its required settings in its area README. The current task reminder script uses Python's standard library, so local preview and tests need no virtual environment.
