import unittest
from unittest.mock import Mock, patch

from bot.config import Settings
from bot.__main__ import main


def make_settings(reminder_enabled: bool) -> Settings:
    return Settings(
        napcat_ws_url="ws://127.0.0.1:3001",
        napcat_ws_token="",
        dashscope_api_key="test-key",
        qwen_base_url="https://example.test/v1",
        qwen_model="qwen-plus",
        qwen_timeout=10.0,
        qwen_system_prompt="system",
        reply_group_messages=True,
        reminder_enabled=reminder_enabled,
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


class MainIntegrationTests(unittest.TestCase):
    @patch("bot.__main__.NapCatBot")
    @patch("bot.__main__.ReminderScheduler")
    @patch("bot.__main__.ReminderService")
    @patch("bot.__main__.QwenClient")
    @patch("bot.__main__.load_settings")
    @patch("bot.__main__.configure_logging")
    def test_starts_scheduler_before_running_bot(
        self,
        configure_logging: Mock,
        load_settings: Mock,
        qwen_class: Mock,
        service_class: Mock,
        scheduler_class: Mock,
        bot_class: Mock,
    ) -> None:
        load_settings.return_value = make_settings(reminder_enabled=True)
        bot = bot_class.return_value
        qwen = qwen_class.return_value
        scheduler = scheduler_class.return_value

        main()

        configure_logging.assert_called_once_with()
        qwen_class.assert_called_once()
        service_class.assert_called_once()
        scheduler.start.assert_called_once_with()
        bot.run.assert_called_once_with()
        scheduler.stop.assert_called_once_with()

    @patch("bot.__main__.NapCatBot")
    @patch("bot.__main__.ReminderScheduler")
    @patch("bot.__main__.ReminderService")
    @patch("bot.__main__.QwenClient")
    @patch("bot.__main__.load_settings")
    @patch("bot.__main__.configure_logging")
    def test_does_not_start_scheduler_when_disabled(
        self,
        configure_logging: Mock,
        load_settings: Mock,
        qwen_class: Mock,
        service_class: Mock,
        scheduler_class: Mock,
        bot_class: Mock,
    ) -> None:
        load_settings.return_value = make_settings(reminder_enabled=False)

        main()

        scheduler_class.assert_not_called()
        service_class.assert_not_called()
        bot_class.return_value.run.assert_called_once_with()

    @patch("bot.__main__.NapCatBot")
    @patch("bot.__main__.load_settings")
    @patch("bot.__main__.configure_logging")
    def test_missing_api_key_exits_before_creating_bot(
        self,
        configure_logging: Mock,
        load_settings: Mock,
        bot_class: Mock,
    ) -> None:
        load_settings.return_value = make_settings(reminder_enabled=True)
        load_settings.return_value = Settings(
            **{
                **load_settings.return_value.__dict__,
                "dashscope_api_key": "",
            }
        )

        with self.assertRaises(SystemExit):
            main()

        bot_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
