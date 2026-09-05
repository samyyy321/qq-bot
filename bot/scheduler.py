from __future__ import annotations

from datetime import datetime
import logging
import threading
from typing import Callable
from zoneinfo import ZoneInfo

from .config import Settings


logger = logging.getLogger("napcat-echo-bot")


class ReminderScheduler:
    """按配置时区检查并执行每日提醒任务。"""

    def __init__(
        self,
        service,
        settings: Settings,
        now_provider: Callable[[], datetime] | None = None,
        check_interval: float = 1.0,
    ) -> None:
        self.service = service
        self.settings = settings
        self.now_provider = now_provider or (
            lambda: datetime.now(ZoneInfo(settings.reminder_timezone))
        )
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._executed_tasks: set[str] = set()
        self._date_key: str | None = None

    @property
    def is_running(self) -> bool:
        """返回调度线程当前是否正在运行。"""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """启动后台调度线程，重复调用不会创建多个线程。"""
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="reminder-scheduler",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """停止后台调度线程，并等待其退出。"""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(self.check_interval + 1.0, 2.0))

    def check_once(self, now: datetime) -> None:
        """检查当前分钟，并执行尚未执行的匹配任务。"""
        local_now = now.astimezone(ZoneInfo(self.settings.reminder_timezone))
        date_key = local_now.date().isoformat()
        if self._date_key != date_key:
            self._date_key = date_key
            self._executed_tasks.clear()

        task_kind = self._task_kind_for_time(local_now.strftime("%H:%M"))
        if task_kind is None:
            return

        task_key = f"{date_key}:{task_kind}:{local_now.strftime('%H:%M')}"
        if task_key in self._executed_tasks:
            return
        self._executed_tasks.add(task_key)

        try:
            self.service.send_reminder(task_kind, local_now)
        except Exception:
            logger.exception("执行定时提醒任务失败: %s", task_kind)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.check_once(self.now_provider())
            except Exception:
                logger.exception("定时提醒调度循环发生异常")
            self._stop_event.wait(self.check_interval)

    def _task_kind_for_time(self, time_text: str) -> str | None:
        if time_text == self.settings.reminder_morning_time:
            return "morning"
        if time_text == self.settings.reminder_night_time:
            return "night"
        if time_text in self.settings.reminder_water_times:
            return "water"
        return None
