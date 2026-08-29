import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "123,456"

import bot as bot_module


class TelegramAuthorizationTests(unittest.TestCase):
    def test_only_configured_operator_chats_are_accepted(self):
        self.assertTrue(bot_module._is_operator(123))
        self.assertTrue(bot_module._is_operator(456))
        self.assertFalse(bot_module._is_operator(999))

    def test_authorization_parser_deduplicates_scope_and_extracts_ticket(self):
        scope, ticket = bot_module._parse_authorization_args(
            "/authorize example.com,192.0.2.0/24 example.com ticket=ENG-42"
        )
        self.assertEqual(scope, ("example.com", "192.0.2.0/24"))
        self.assertEqual(ticket, "ENG-42")


if __name__ == "__main__":
    unittest.main()

