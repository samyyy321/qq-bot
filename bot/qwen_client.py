from __future__ import annotations

from typing import Any

from openai import OpenAI

from .config import Settings


class QwenClient:
    """使用百炼 OpenAI 兼容接口调用 Qwen 的客户端。"""

    def __init__(self, settings: Settings, sdk_client: Any | None = None) -> None:
        self.model = settings.qwen_model
        self.system_prompt = settings.qwen_system_prompt
        self._client = sdk_client or OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.qwen_base_url,
            timeout=settings.qwen_timeout,
            max_retries=2,
        )

    def generate(self, user_text: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_text},
            ],
        )
        content = response.choices[0].message.content
        if not content or not str(content).strip():
            raise ValueError("Qwen 返回了空消息")
        return str(content).strip()
