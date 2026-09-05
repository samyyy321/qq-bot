from __future__ import annotations

from datetime import datetime
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from bot.config import Settings
from bot.reminder_service import ReminderService


class FakeQwen:
    def __init__(self, reply: str = "模型回答", error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.inputs: list[str] = []

    def generate(self, user_text: str) -> str:
        self.inputs.append(user_text)
        if self.error:
            raise self.error
        return self.reply


def make_settings() -> Settings:
    return Settings(
        napcat_ws_url="ws://127.0.0.1:3001",
        napcat_ws_token="",
        dashscope_api_key="test-key",
        qwen_base_url="https://example.test/v1",
        qwen_model="qwen-plus",
        qwen_timeout=10.0,
        qwen_system_prompt="system",
        reply_group_messages=True,
        reminder_enabled=True,
        reminder_group_ids=(1036995638, 1234567890),
        reminder_timezone="Asia/Shanghai",
        reminder_morning_time="09:00",
        reminder_night_time="21:00",
        reminder_water_times=("09:15", "09:30", "20:45"),
        reminder_water_messages=("请记得喝水。", "补充水分啦。"),
    )


class ReminderServiceTests(unittest.TestCase):
    def test_morning_uses_qwen_with_date_weekday_and_weather_notice(self) -> None:
        qwen = FakeQwen("早安回答")
        sent: list[tuple[int | str, str]] = []
        service = ReminderService(make_settings(), qwen, lambda group, text: sent.append((group, text)))
        now = datetime(2026, 9, 5, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        service.send_morning(now)

        self.assertIn("2026 年 9 月 5 日", qwen.inputs[0])
        self.assertIn("星期六", qwen.inputs[0])
        self.assertIn("天气信息暂未配置", qwen.inputs[0])
        self.assertEqual(sent, [(1036995638, "早安回答"), (1234567890, "早安回答")])

    def test_water_uses_one_configured_message_without_calling_qwen(self) -> None:
        qwen = FakeQwen()
        sent: list[tuple[int | str, str]] = []
        service = ReminderService(make_settings(), qwen, lambda group, text: sent.append((group, text)))

        with patch("bot.reminder_service.random.choice", return_value="补充水分啦。"):
            service.send_water(datetime(2026, 9, 5, 9, 15, tzinfo=ZoneInfo("Asia/Shanghai")))

        self.assertEqual(qwen.inputs, [])
        self.assertEqual(sent, [(1036995638, "补充水分啦。"), (1234567890, "补充水分啦。")])

    def test_night_uses_qwen_with_rest_prompt(self) -> None:
        qwen = FakeQwen("晚安回答")
        sent: list[tuple[int | str, str]] = []
        service = ReminderService(make_settings(), qwen, lambda group, text: sent.append((group, text)))

        service.send_night(datetime(2026, 9, 5, 21, 0, tzinfo=ZoneInfo("Asia/Shanghai")))

        self.assertIn("早点休息", qwen.inputs[0])
        self.assertEqual(sent, [(1036995638, "晚安回答"), (1234567890, "晚安回答")])

    def test_failed_group_does_not_block_other_groups(self) -> None:
        sent: list[int | str] = []

        def send(group_id: int | str, text: str) -> None:
            if group_id == 1036995638:
                raise RuntimeError("send failed")
            sent.append(group_id)

        service = ReminderService(make_settings(), FakeQwen(), send)
        service.send_water(datetime(2026, 9, 5, 11, 0, tzinfo=ZoneInfo("Asia/Shanghai")))

        self.assertEqual(sent, [1234567890])


if __name__ == "__main__":
    unittest.main()
