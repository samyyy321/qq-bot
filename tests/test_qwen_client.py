import unittest

from bot.config import Settings
from bot.qwen_client import QwenClient


class FakeCompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Message", (), {"content": self.content})()},
                    )()
                ]
            },
        )()


class FakeSDKClient:
    def __init__(self, content: str) -> None:
        self.completions = FakeCompletions(content)
        self.chat = type("Chat", (), {"completions": self.completions})()


def make_settings() -> Settings:
    return Settings(
        napcat_ws_url="ws://127.0.0.1:3001",
        napcat_ws_token="",
        dashscope_api_key="test-key",
        qwen_base_url="https://example.test/v1",
        qwen_model="qwen-plus",
        qwen_timeout=10.0,
        qwen_system_prompt="test system prompt",
        reply_group_messages=True,
    )


class QwenClientTests(unittest.TestCase):
    def test_generates_text_with_configured_model_and_prompts(self) -> None:
        sdk_client = FakeSDKClient("  你好  ")
        client = QwenClient(make_settings(), sdk_client=sdk_client)

        self.assertEqual(client.generate("hello"), "你好")
        call = sdk_client.completions.calls[0]
        self.assertEqual(call["model"], "qwen-plus")
        self.assertEqual(call["messages"][0], {"role": "system", "content": "test system prompt"})
        self.assertEqual(call["messages"][1], {"role": "user", "content": "hello"})

    def test_rejects_empty_response(self) -> None:
        client = QwenClient(make_settings(), sdk_client=FakeSDKClient("  "))

        with self.assertRaises(ValueError):
            client.generate("hello")


if __name__ == "__main__":
    unittest.main()
