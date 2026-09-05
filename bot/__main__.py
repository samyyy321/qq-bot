from __future__ import annotations

import logging

from .config import load_settings
from .logging_config import configure_logging
from .onebot_client import NapCatBot
from .qwen_client import QwenClient
from .reminder_service import ReminderService
from .scheduler import ReminderScheduler


logger = logging.getLogger("napcat-echo-bot")


def main() -> None:
    """加载配置、启动定时提醒，并运行 OneBot 客户端。"""
    configure_logging()
    settings = load_settings()
    if not settings.dashscope_api_key:
        raise SystemExit(
            "未配置 DASHSCOPE_API_KEY，请在项目根目录 .env 中填写阿里云百炼 API Key。"
        )

    logger.info("私聊 Qwen 回复：开启")
    logger.info(
        "群聊 @机器人 Qwen 回复：%s",
        "开启" if settings.reply_group_messages else "关闭",
    )

    qwen_client = QwenClient(settings)
    napcat_bot = NapCatBot(settings, qwen_client=qwen_client)
    reminder_scheduler: ReminderScheduler | None = None

    if settings.reminder_enabled:
        reminder_service = ReminderService(
            settings,
            qwen_client,
            napcat_bot.send_group_message,
        )
        reminder_scheduler = ReminderScheduler(reminder_service, settings)
        if settings.reminder_group_ids:
            reminder_scheduler.start()
            logger.info(
                "定时提醒已开启：时区=%s，目标群数量=%s",
                settings.reminder_timezone,
                len(settings.reminder_group_ids),
            )
        else:
            logger.warning("定时提醒未启动：未配置 REMINDER_GROUP_IDS")
    else:
        logger.info("定时提醒：关闭")

    try:
        napcat_bot.run()
    finally:
        if reminder_scheduler is not None:
            reminder_scheduler.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已停止 QQ Bot")
