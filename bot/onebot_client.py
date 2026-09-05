from __future__ import annotations

import json
import logging
import threading
import uuid
from typing import Any, Callable

import websocket

from .config import Settings
from .message_parser import extract_group_at_text, is_self_message
from .qwen_client import QwenClient


logger = logging.getLogger("napcat-echo-bot")
FALLBACK_REPLY = "抱歉，我暂时无法处理这个问题。"
EMPTY_MENTION_PROMPT = "请向我打个招呼。"


class NapCatBot:
    """通过 Qwen 处理消息的 OneBot 11 WebSocket 客户端。"""

    def __init__(
        self,
        settings: Settings,
        qwen_client: QwenClient | Any | None = None,
    ) -> None:
        self.settings = settings
        self.qwen_client = qwen_client or QwenClient(settings)
        self.ws: websocket.WebSocketApp | None = None
        self._send_lock = threading.Lock()

    def run(self) -> None:
        """创建 WebSocket 客户端并持续连接 NapCat。"""
        headers = (
            [f"Authorization: Bearer {self.settings.napcat_ws_token}"]
            if self.settings.napcat_ws_token
            else None
        )
        self.ws = websocket.WebSocketApp(
            self.settings.napcat_ws_url,
            header=headers,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        logger.info("正在连接 NapCat: %s", self.settings.napcat_ws_url)
        self.ws.run_forever()

    def handle_event(self, event: dict[str, Any]) -> None:
        """筛选 OneBot 事件，并分发私聊或群聊消息。"""
        if event.get("post_type") != "message":
            return

        # 忽略机器人自身消息
        if is_self_message(event):
            logger.info("忽略机器人自身消息")
            return

        # 处理私聊消息
        message_type = event.get("message_type")
        if message_type == "private":
            user_id = event.get("user_id")
            user_text = str(event.get("raw_message") or "").strip()
            if user_id is None or not user_text:
                logger.warning("私聊事件缺少 user_id 或消息文本，跳过回复")
                return
            self._reply_with_qwen(
                lambda reply: self.send_private_message(user_id, reply),
                user_text,
            )
            return

        # 处理群聊消息 
        if message_type == "group" and self.settings.reply_group_messages:
            group_id = event.get("group_id")
            if group_id is None:
                logger.warning("群聊事件缺少 group_id，跳过回复")
                return

            user_text = extract_group_at_text(event)
            if user_text is None:
                return

            self._reply_with_qwen(
                lambda reply: self.send_group_message(group_id, reply),
                user_text or EMPTY_MENTION_PROMPT,
            )

    def _on_message(self, ws: websocket.WebSocketApp, raw_message: str) -> None:
        """解析 NapCat 推送的 JSON 消息，并交给事件处理函数。"""
        try:
            event: dict[str, Any] = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning("收到非 JSON 消息: %s", raw_message)
            return

        logger.info("收到事件:\n%s", json.dumps(event, ensure_ascii=False, indent=2))
        self.handle_event(event)

    def _reply_with_qwen(self, send_reply: Callable[[str], None], user_text: str) -> None:
        """调用 Qwen 生成回复，失败时发送统一的兜底消息。"""
        try:
            reply = self.qwen_client.generate(user_text)
        except Exception:
            logger.exception("调用 Qwen 失败")
            reply = FALLBACK_REPLY
        send_reply(reply)

    def send_private_message(self, user_id: int | str, message: str) -> None:
        """调用 OneBot API 向指定用户发送私聊消息。"""
        self._call_api(
            "send_private_msg",
            {"user_id": int(user_id), "message": message},
        )

    def send_group_message(self, group_id: int | str, message: str) -> None:
        """调用 OneBot API 向指定群发送群聊消息。"""
        self._call_api(
            "send_group_msg",
            {"group_id": int(group_id), "message": message},
        )

    def _call_api(self, action: str, params: dict[str, Any]) -> None:
        """组装并通过 WebSocket 发送 OneBot API 请求。"""
        if self.ws is None:
            logger.error("WebSocket 尚未建立，无法调用 %s", action)
            return

        request = {"action": action, "params": params, "echo": str(uuid.uuid4())}
        payload = json.dumps(request, ensure_ascii=False)
        with self._send_lock:
            self.ws.send(payload)
        logger.info("已调用 %s: %s", action, json.dumps(params, ensure_ascii=False))

    @staticmethod
    def _on_open(ws: websocket.WebSocketApp) -> None:
        """记录 WebSocket 连接成功日志。"""
        logger.info("已连接到 NapCat WebSocket")

    @staticmethod
    def _on_error(ws: websocket.WebSocketApp, error: Any) -> None:
        """记录 WebSocket 运行错误日志。"""
        logger.error("WebSocket 错误: %s", error)

    @staticmethod
    def _on_close(
        ws: websocket.WebSocketApp,
        close_status_code: int | None,
        close_msg: str | None,
    ) -> None:
        """记录 WebSocket 断开日志及关闭原因。"""
        logger.info("WebSocket 已断开，code=%s, reason=%s", close_status_code, close_msg)
