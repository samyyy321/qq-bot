from __future__ import annotations

from datetime import datetime
import threading
import time
import unittest
from zoneinfo import ZoneInfo

from bot.config import Settings
from bot.scheduler import ReminderScheduler


class FakeReminderService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, datetime]] = []

    def send_reminder(self, kind: str, now: datetime) -> None:
        self.calls.append((kind, now))


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
        reminder_group_ids=(1036995638,),
        reminder_timezone="Asia/Shanghai",
        reminder_morning_time="09:00",
        reminder_night_time="21:00",
        reminder_water_times=tuple(
            f"{hour:02d}:{minute:02d}"
            for hour in range(9, 21)
            for minute in range(0, 60, 15)
            if not (hour == 9 and minute == 0)
        ),
        reminder_water_messages=("请记得喝水。",),
    )


class ReminderSchedulerTests(unittest.TestCase):
    def test_triggers_morning_once_per_minute(self) -> None:
        service = FakeReminderService()
        scheduler = ReminderScheduler(service, make_settings())
        now = datetime(2026, 9, 5, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        scheduler.check_once(now)
        scheduler.check_once(now)

        self.assertEqual([kind for kind, _ in service.calls], ["morning"])

    def test_triggers_each_water_time_and_night(self) -> None:
        service = FakeReminderService()
        scheduler = ReminderScheduler(service, make_settings())
        timezone = ZoneInfo("Asia/Shanghai")

        for hour, minute in ((9, 15), (9, 30), (10, 0), (20, 45)):
            scheduler.check_once(datetime(2026, 9, 5, hour, minute, tzinfo=timezone))
        scheduler.check_once(datetime(2026, 9, 5, 21, 0, tzinfo=timezone))

        self.assertEqual(
            [kind for kind, _ in service.calls],
            ["water", "water", "water", "water", "night"],
        )

    def test_nine_and_night_are_not_water_times(self) -> None:
        service = FakeReminderService()
        scheduler = ReminderScheduler(service, make_settings())
        timezone = ZoneInfo("Asia/Shanghai")

        scheduler.check_once(datetime(2026, 9, 5, 9, 0, tzinfo=timezone))
        scheduler.check_once(datetime(2026, 9, 5, 21, 0, tzinfo=timezone))

        self.assertEqual([kind for kind, _ in service.calls], ["morning", "night"])

    def test_does_not_replay_missed_morning_reminder(self) -> None:
        service = FakeReminderService()
        scheduler = ReminderScheduler(service, make_settings())

        scheduler.check_once(datetime(2026, 9, 5, 10, 5, tzinfo=ZoneInfo("Asia/Shanghai")))

        self.assertEqual(service.calls, [])

    def test_non_scheduled_time_does_nothing(self) -> None:
        service = FakeReminderService()
        scheduler = ReminderScheduler(service, make_settings())

        scheduler.check_once(datetime(2026, 9, 5, 10, 7, tzinfo=ZoneInfo("Asia/Shanghai")))

        self.assertEqual(service.calls, [])

    def test_stop_ends_background_thread(self) -> None:
        service = FakeReminderService()
        scheduler = ReminderScheduler(service, make_settings(), check_interval=0.01)

        scheduler.start()
        time.sleep(0.03)
        scheduler.stop()

        self.assertFalse(scheduler.is_running)


if __name__ == "__main__":
    unittest.main()
