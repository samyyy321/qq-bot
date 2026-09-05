import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bot.config import load_settings


class SettingsTests(unittest.TestCase):
    def test_environment_variables_override_dotenv_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "QWEN_MODEL=from-dotenv\n"
                "QWEN_TIMEOUT=12\n"
                "ECHO_REPLY_GROUP_MESSAGES=false\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"QWEN_MODEL": "from-environment"}, clear=True):
                settings = load_settings(env_file)

        self.assertEqual(settings.qwen_model, "from-environment")
        self.assertEqual(settings.qwen_timeout, 12.0)
        self.assertFalse(settings.reply_group_messages)

    def test_uses_safe_defaults_without_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {}, clear=True):
                settings = load_settings(Path(directory) / ".env")

        self.assertEqual(settings.napcat_ws_url, "ws://127.0.0.1:3001")
        self.assertEqual(settings.qwen_model, "qwen-plus")
        self.assertEqual(settings.dashscope_api_key, "")
        self.assertTrue(settings.reply_group_messages)

    def test_parses_reminder_configuration(self) -> None:
        with patch.dict(
            os.environ,
            {
                "REMINDER_ENABLED": "true",
                "REMINDER_GROUP_IDS": "1036995638, 1234567890",
                "REMINDER_TIMEZONE": "Asia/Shanghai",
                "REMINDER_MORNING_TIME": "09:00",
                "REMINDER_NIGHT_TIME": "21:00",
                "REMINDER_WATER_MESSAGES": "请喝水||记得补水||休息一下喝口水",
            },
            clear=True,
        ):
            settings = load_settings(Path("missing.env"))

        self.assertTrue(settings.reminder_enabled)
        self.assertEqual(settings.reminder_group_ids, (1036995638, 1234567890))
        self.assertEqual(settings.reminder_timezone, "Asia/Shanghai")
        self.assertEqual(
            settings.reminder_water_times,
            tuple(
                f"{hour:02d}:{minute:02d}"
                for hour in range(9, 21)
                for minute in range(0, 60, 15)
                if not (hour == 9 and minute == 0)
            ),
        )
        self.assertEqual(
            settings.reminder_water_messages,
            ("请喝水", "记得补水", "休息一下喝口水"),
        )

    def test_rejects_invalid_reminder_group_id(self) -> None:
        with patch.dict(os.environ, {"REMINDER_GROUP_IDS": "1036995638,nope"}, clear=True):
            with self.assertRaisesRegex(ValueError, "REMINDER_GROUP_IDS"):
                load_settings(Path("missing.env"))

    def test_rejects_invalid_reminder_time(self) -> None:
        with patch.dict(os.environ, {"REMINDER_MORNING_TIME": "9am"}, clear=True):
            with self.assertRaisesRegex(ValueError, "REMINDER_MORNING_TIME"):
                load_settings(Path("missing.env"))


if __name__ == "__main__":
    unittest.main()
