from __future__ import annotations

import logging

from .config import load_settings
from .logging_config import configure_logging
from .onebot_client import NapCatBot


logger = logging.getLogger("napcat-echo-bot")


def main() -> None:
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
    NapCatBot(settings).run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已停止 QQ Bot")
