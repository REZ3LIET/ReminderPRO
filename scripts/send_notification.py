"""Post a generated reminder message to a Slack or Discord incoming webhook."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_message(provider: str, webhook: str, message: str) -> None:
    if provider not in {"discord", "slack"}:
        raise ValueError("NOTIFICATION_PROVIDER must be 'discord' or 'slack'")
    if not message:
        raise ValueError("Generated message is empty")
    if provider == "discord" and len(message) > 2000:
        raise ValueError("Discord messages are limited to 2000 characters; shorten the task report or use Slack")
    payload = {"content": message, "allowed_mentions": {"parse": []}} if provider == "discord" else {"text": message}
    request = Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            if response.status not in (200, 204):
                raise ValueError(f"Webhook returned HTTP {response.status}")
    except HTTPError as exc:
        raise ValueError(f"Webhook returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise ValueError(f"Webhook request failed: {exc.reason}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message_file", type=Path)
    args = parser.parse_args()
    provider = os.environ.get("NOTIFICATION_PROVIDER", "discord").lower()
    if provider not in {"discord", "slack"}:
        raise SystemExit("NOTIFICATION_PROVIDER must be 'discord' or 'slack'")
    webhook = os.environ.get(f"{provider.upper()}_WEBHOOK_URL")
    if not webhook:
        raise SystemExit(f"Missing {provider.upper()}_WEBHOOK_URL secret")
    message = args.message_file.read_text(encoding="utf-8").strip()
    try:
        post_message(provider, webhook, message)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Reminder sent to {provider}")


if __name__ == "__main__":
    main()
