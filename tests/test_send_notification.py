import json
import unittest
from unittest.mock import MagicMock, patch

from scripts.send_notification import post_message


class NotificationTests(unittest.TestCase):
    @patch("scripts.send_notification.urlopen")
    def test_discord_payload_suppresses_mentions(self, open_url):
        response = MagicMock(status=204)
        open_url.return_value.__enter__.return_value = response
        post_message("discord", "https://example.invalid/webhook", "📋 Task Status")
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data), {
            "content": "📋 Task Status",
            "allowed_mentions": {"parse": []},
        })

    @patch("scripts.send_notification.urlopen")
    def test_slack_payload_uses_text(self, open_url):
        response = MagicMock(status=200)
        open_url.return_value.__enter__.return_value = response
        post_message("slack", "https://example.invalid/webhook", "📋 Task Status")
        request = open_url.call_args.args[0]
        self.assertEqual(json.loads(request.data), {"text": "📋 Task Status"})

    @patch("scripts.send_notification.urlopen")
    def test_discord_over_limit_does_not_post(self, open_url):
        with self.assertRaisesRegex(ValueError, "2000 characters"):
            post_message("discord", "https://example.invalid/webhook", "x" * 2001)
        open_url.assert_not_called()


if __name__ == "__main__":
    unittest.main()
