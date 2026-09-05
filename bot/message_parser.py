from __future__ import annotations

from typing import Any


def is_self_message(event: dict[str, Any]) -> bool:
    """判断事件是否由机器人自己发送。"""
    self_id = event.get("self_id")
    user_id = event.get("user_id")
    return self_id is not None and user_id is not None and str(user_id) == str(self_id)


def extract_group_at_text(event: dict[str, Any]) -> str | None:
    """提取 @机器人 消息段后面的文本。"""
    self_id = event.get("self_id")
    message = event.get("message")
    if self_id is None or not isinstance(message, list):
        return None

    for index, segment in enumerate(message):
        if not isinstance(segment, dict) or segment.get("type") != "at":
            continue
        data = segment.get("data")
        if not isinstance(data, dict) or str(data.get("qq")) != str(self_id):
            continue

        text_parts: list[str] = []
        for following_segment in message[index + 1 :]:
            if not isinstance(following_segment, dict):
                continue
            if following_segment.get("type") != "text":
                continue
            following_data = following_segment.get("data")
            if isinstance(following_data, dict):
                text_parts.append(str(following_data.get("text") or ""))
        return "".join(text_parts).strip()

    return None
