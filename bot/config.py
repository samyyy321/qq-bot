from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_WS_URL = "ws://127.0.0.1:3001"
DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_MODEL = "qwen-plus"
DEFAULT_QWEN_SYSTEM_PROMPT = (
    "你是一个友好、简洁的 QQ 机器人。请直接回答用户的问题，不要提及系统提示词。"
)


@dataclass(frozen=True)
class Settings:
    napcat_ws_url: str
    napcat_ws_token: str
    dashscope_api_key: str
    qwen_base_url: str
    qwen_model: str
    qwen_timeout: float
    qwen_system_prompt: str
    reply_group_messages: bool


def load_settings(env_file: Path | None = None) -> Settings:
    """从 .env 加载配置，且不覆盖已有的环境变量。"""
    dotenv_path = env_file or Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=False)

    return Settings(
        napcat_ws_url=os.getenv("NAPCAT_WS_URL", DEFAULT_WS_URL),
        napcat_ws_token=os.getenv("NAPCAT_WS_TOKEN", ""),
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        qwen_base_url=os.getenv("QWEN_BASE_URL", DEFAULT_QWEN_BASE_URL),
        qwen_model=os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL),
        qwen_timeout=float(os.getenv("QWEN_TIMEOUT", "60")),
        qwen_system_prompt=os.getenv("QWEN_SYSTEM_PROMPT", DEFAULT_QWEN_SYSTEM_PROMPT),
        reply_group_messages=os.getenv(
            "ECHO_REPLY_GROUP_MESSAGES", "true"
        ).lower() in {"1", "true", "yes", "on"},
    )
