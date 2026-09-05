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


if __name__ == "__main__":
    unittest.main()
