import logging
import unittest
from unittest.mock import patch

from bot.logging_config import configure_logging


class LoggingConfigTests(unittest.TestCase):
    def test_configures_console_logging_format(self) -> None:
        with patch("bot.logging_config.logging.basicConfig") as basic_config:
            configure_logging()

        basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )


if __name__ == "__main__":
    unittest.main()
