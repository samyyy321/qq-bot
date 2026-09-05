from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


DEFAULT_WS_URL = "ws://127.0.0.1:3001"
DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_MODEL = "qwen-plus"
DEFAULT_QWEN_SYSTEM_PROMPT = (
    "你是一个友好、简洁的 QQ 机器人。请直接回答用户的问题，不要提及系统提示词。"
)
DEFAULT_REMINDER_TIMEZONE = "Asia/Shanghai"
DEFAULT_REMINDER_MORNING_TIME = "09:00"
DEFAULT_REMINDER_NIGHT_TIME = "21:00"
DEFAULT_REMINDER_WATER_START = "09:15"
DEFAULT_REMINDER_WATER_END = "20:45"
DEFAULT_REMINDER_WATER_INTERVAL_MINUTES = 15
DEFAULT_REMINDER_WATER_MESSAGES = ("现在是喝水时间，记得补充水分哦～",)


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
    reminder_enabled: bool = True
    reminder_group_ids: tuple[int, ...] = ()
    reminder_timezone: str = DEFAULT_REMINDER_TIMEZONE
    reminder_morning_time: str = DEFAULT_REMINDER_MORNING_TIME
    reminder_night_time: str = DEFAULT_REMINDER_NIGHT_TIME
    reminder_water_times: tuple[str, ...] = ()
    reminder_water_messages: tuple[str, ...] = DEFAULT_REMINDER_WATER_MESSAGES


def _parse_bool(value: str, field_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{field_name} 必须是 true 或 false")


def _parse_group_ids(raw: str) -> tuple[int, ...]:
    if not raw.strip():
        return ()

    group_ids: list[int] = []
    for item in raw.split(","):
        value = item.strip()
        try:
            group_id = int(value)
        except ValueError as exc:
            raise ValueError(f"REMINDER_GROUP_IDS 包含无效群号: {value}") from exc
        if group_id <= 0:
            raise ValueError(f"REMINDER_GROUP_IDS 必须是正整数: {value}")
        group_ids.append(group_id)
    return tuple(group_ids)


def _parse_time(value: str, field_name: str) -> str:
    normalized = value.strip()
    try:
        parsed = datetime.strptime(normalized, "%H:%M")
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须使用 HH:MM 格式: {value}") from exc
    return parsed.strftime("%H:%M")


def _parse_time_list(raw: str, field_name: str) -> tuple[str, ...]:
    if not raw.strip():
        return ()
    return tuple(_parse_time(item, field_name) for item in raw.split(","))


def _validate_timezone(value: str) -> str:
    normalized = value.strip()
    try:
        ZoneInfo(normalized)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"REMINDER_TIMEZONE 无效: {value}") from exc
    return normalized


def _parse_messages(raw: str) -> tuple[str, ...]:
    messages = tuple(item.strip() for item in raw.split("||") if item.strip())
    if not messages:
        raise ValueError("REMINDER_WATER_MESSAGES 不能是空值")
    return messages


def _water_times() -> tuple[str, ...]:
    start = datetime.strptime(DEFAULT_REMINDER_WATER_START, "%H:%M")
    end = datetime.strptime(DEFAULT_REMINDER_WATER_END, "%H:%M")
    times: list[str] = []
    current = start
    while current <= end:
        times.append(current.strftime("%H:%M"))
        current += timedelta(minutes=DEFAULT_REMINDER_WATER_INTERVAL_MINUTES)
    return tuple(times)


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
        reply_group_messages=_parse_bool(
            os.getenv("ECHO_REPLY_GROUP_MESSAGES", "true"),
            "ECHO_REPLY_GROUP_MESSAGES",
        ),
        reminder_enabled=_parse_bool(
            os.getenv("REMINDER_ENABLED", "true"),
            "REMINDER_ENABLED",
        ),
        reminder_group_ids=_parse_group_ids(os.getenv("REMINDER_GROUP_IDS", "")),
        reminder_timezone=_validate_timezone(
            os.getenv("REMINDER_TIMEZONE", DEFAULT_REMINDER_TIMEZONE)
        ),
        reminder_morning_time=_parse_time(
            os.getenv("REMINDER_MORNING_TIME", DEFAULT_REMINDER_MORNING_TIME),
            "REMINDER_MORNING_TIME",
        ),
        reminder_night_time=_parse_time(
            os.getenv("REMINDER_NIGHT_TIME", DEFAULT_REMINDER_NIGHT_TIME),
            "REMINDER_NIGHT_TIME",
        ),
        reminder_water_times=_water_times(),
        reminder_water_messages=_parse_messages(
            os.getenv(
                "REMINDER_WATER_MESSAGES",
                "||".join(DEFAULT_REMINDER_WATER_MESSAGES),
            )
        ),
    )
