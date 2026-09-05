from __future__ import annotations

from datetime import datetime
import logging
import random
import threading
from typing import Callable

from .config import Settings


logger = logging.getLogger("napcat-echo-bot")


class ReminderService:
    """生成定时提醒内容，并发送到配置的群。"""

    def __init__(
        self,
        settings: Settings,
        qwen_client,
        send_group_message: Callable[[int | str, str], None],
    ) -> None:
        self.settings = settings
        self.qwen_client = qwen_client
        self.send_group_message = send_group_message

    def send_reminder(self, kind: str, now: datetime) -> None:
        """按提醒类型生成内容并发送到所有目标群。"""
        if kind == "morning":
            content = self._morning_content(now)
        elif kind == "water":
            content = random.choice(self.settings.reminder_water_messages)
        elif kind == "night":
            content = self._night_content(now)
        else:
            raise ValueError(f"未知提醒类型: {kind}")
        self._send_to_groups(content)

    def send_morning(self, now: datetime) -> None:
        """生成并发送早间提醒。"""
        self.send_reminder("morning", now)

    def send_water(self, now: datetime) -> None:
        """发送固定文本的喝水提醒。"""
        self.send_reminder("water", now)

    def send_night(self, now: datetime) -> None:
        """生成并发送晚间休息提醒。"""
        self.send_reminder("night", now)

    def _morning_content(self, now: datetime) -> str:
        prompt = (
            f"今天是 {now.year} 年 {now.month} 月 {now.day} 日，"
            f"{self._weekday_text(now)}。\n"
            "天气信息暂未配置。\n"
            "请生成一段简短、自然、适合发送到 QQ 群的早安提醒。"
        )
        try:
            return self.qwen_client.generate(prompt)
        except Exception:
            logger.exception("生成早间提醒失败")
            return "早上好，今天也要保持好心情，开启充实的一天。"

    def _night_content(self, now: datetime) -> str:
        del now
        prompt = "现在是晚上 9 点。请生成一段简短、自然、提醒 QQ 群成员早点休息的话。"
        try:
            return self.qwen_client.generate(prompt)
        except Exception:
            logger.exception("生成晚间提醒失败")
            return "时间不早了，提醒大家早点休息，保持充足睡眠。"

    def _send_to_groups(self, content: str) -> None:
        if not self.settings.reminder_group_ids:
            logger.warning("未配置定时提醒目标群，跳过发送")
            return

        for group_id in self.settings.reminder_group_ids:
            try:
                self.send_group_message(group_id, content)
            except Exception:
                logger.exception("向群 %s 发送定时提醒失败", group_id)

    @staticmethod
    def _weekday_text(now: datetime) -> str:
        return ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")[
            now.weekday()
        ]
