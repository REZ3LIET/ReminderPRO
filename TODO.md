# TODO

## Replace GitHub's scheduled trigger with a local cron dispatcher

- [ ] Evaluate and implement an event-driven scheduling option in which a local server invokes the GitHub Actions REST API.

Proposed flow:

```text
Local/server cron
       │
       │ curl POST
       ▼
GitHub Actions API
       │
       │ workflow_dispatch
       ▼
Existing workflow
       │
       ├── checkout
       ├── Python task processing and message generation
       └── Discord / Slack delivery
```

The workflow would use only the manual dispatch event instead of GitHub's scheduled trigger:

```yaml
on:
  workflow_dispatch:
```

A server-side script could dispatch it through the GitHub Actions REST API:

```sh
curl --fail --silent --show-error -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/task-reminders.yml/dispatches \
  -d '{"ref":"main"}'
```

The local cron could then define any required schedules:

```cron
52 9 * * *    /opt/reminders/trigger.sh
0 12 * * *    /opt/reminders/trigger.sh
0 18 * * *    /opt/reminders/trigger.sh
0 22 * * 1-5  /opt/reminders/trigger.sh
```

If one dispatcher needs to select between multiple workflows or tasks, add a dispatch input:

```yaml
on:
  workflow_dispatch:
    inputs:
      task:
        required: true
        type: string
```

Then include the input in the API request:

```sh
-d '{"ref":"main","inputs":{"task":"daily-reminders"}}'
```

Implementation considerations:

- Keep the local cron responsible only for scheduling and dispatch.
- Keep GitHub Actions responsible for checkout, execution, secrets, and provider delivery.
- Use `curl --fail --silent --show-error` so rejected requests return a failure.
- Log dispatch results and consider bounded retry logic.
- Store the GitHub token outside the repository and give it only the access needed to dispatch the workflow.
- Account for the local server being unavailable or disconnected when a cron entry fires.

Do not implement this architecture until it is selected as the scheduling approach.
