import json
import unittest
from unittest.mock import patch

from bot.config import Settings
from bot.onebot_client import FALLBACK_REPLY, NapCatBot


class FakeQwenClient:
    def __init__(self, content: str = "Qwen 回复", error: Exception | None = None) -> None:
        self.content = content
        self.error = error
        self.inputs: list[str] = []

    def generate(self, user_text: str) -> str:
        self.inputs.append(user_text)
        if self.error:
            raise self.error
        return self.content


def make_settings(group_enabled: bool = True) -> Settings:
    return Settings(
        napcat_ws_url="ws://127.0.0.1:3001",
        napcat_ws_token="",
        dashscope_api_key="test-key",
        qwen_base_url="https://example.test/v1",
        qwen_model="qwen-plus",
        qwen_timeout=10.0,
        qwen_system_prompt="system",
        reply_group_messages=group_enabled,
    )


class OneBotEventHandlingTests(unittest.TestCase):
    def test_private_message_calls_qwen_and_sends_private_api(self) -> None:
        qwen = FakeQwenClient("私聊回答")
        bot = NapCatBot(make_settings(), qwen_client=qwen)
        sent: list[tuple[str, dict]] = []
        bot._call_api = lambda action, params: sent.append((action, params))

        bot.handle_event({
            "post_type": "message",
            "message_type": "private",
            "self_id": 2908229650,
            "user_id": 2543642119,
            "raw_message": "你好",
        })

        self.assertEqual(qwen.inputs, ["你好"])
        self.assertEqual(sent, [("send_private_msg", {"user_id": 2543642119, "message": "私聊回答"})])

    def test_group_mention_calls_qwen_and_sends_to_original_group(self) -> None:
        qwen = FakeQwenClient("群聊回答")
        bot = NapCatBot(make_settings(), qwen_client=qwen)
        sent: list[tuple[str, dict]] = []
        bot._call_api = lambda action, params: sent.append((action, params))

        bot.handle_event({
            "post_type": "message",
            "message_type": "group",
            "self_id": 2908229650,
            "user_id": 2543642119,
            "group_id": 1036995638,
            "message": [
                {"type": "at", "data": {"qq": "2908229650"}},
                {"type": "text", "data": {"text": " hello"}},
            ],
        })

        self.assertEqual(qwen.inputs, ["hello"])
        self.assertEqual(sent, [("send_group_msg", {"group_id": 1036995638, "message": "群聊回答"})])

    def test_group_message_without_bot_mention_is_ignored(self) -> None:
        qwen = FakeQwenClient()
        bot = NapCatBot(make_settings(), qwen_client=qwen)

        bot.handle_event({
            "post_type": "message",
            "message_type": "group",
            "self_id": 2908229650,
            "user_id": 2543642119,
            "group_id": 1036995638,
            "message": [{"type": "text", "data": {"text": "普通消息"}}],
        })

        self.assertEqual(qwen.inputs, [])

    def test_self_message_is_ignored(self) -> None:
        qwen = FakeQwenClient()
        bot = NapCatBot(make_settings(), qwen_client=qwen)

        bot.handle_event({
            "post_type": "message",
            "message_type": "private",
            "self_id": 2908229650,
            "user_id": "2908229650",
            "raw_message": "自己的消息",
        })

        self.assertEqual(qwen.inputs, [])

    def test_qwen_failure_sends_fallback_without_exposing_exception(self) -> None:
        qwen = FakeQwenClient(error=RuntimeError("provider unavailable"))
        bot = NapCatBot(make_settings(), qwen_client=qwen)
        sent: list[tuple[str, dict]] = []
        bot._call_api = lambda action, params: sent.append((action, params))

        with patch("bot.onebot_client.logger.exception") as log_exception:
            bot.handle_event({
                "post_type": "message",
                "message_type": "private",
                "self_id": 2908229650,
                "user_id": 2543642119,
                "raw_message": "你好",
            })

        self.assertEqual(sent[0], ("send_private_msg", {"user_id": 2543642119, "message": FALLBACK_REPLY}))
        log_exception.assert_called_once()

    def test_invalid_json_is_ignored(self) -> None:
        bot = NapCatBot(make_settings(), qwen_client=FakeQwenClient())

        with patch("bot.onebot_client.logger.warning") as log_warning:
            bot._on_message(None, "not-json")

        log_warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
