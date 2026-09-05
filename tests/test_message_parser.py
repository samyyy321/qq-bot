import unittest

from bot.message_parser import extract_group_at_text, is_self_message


class MessageParserTests(unittest.TestCase):
    def test_extracts_text_after_atting_bot(self) -> None:
        event = {
            "self_id": 2908229650,
            "message": [
                {"type": "at", "data": {"qq": "2908229650"}},
                {"type": "text", "data": {"text": " hello"}},
            ],
        }

        self.assertEqual(extract_group_at_text(event), "hello")

    def test_ignores_atting_another_member(self) -> None:
        event = {
            "self_id": 2908229650,
            "message": [
                {"type": "at", "data": {"qq": "2543642119"}},
                {"type": "text", "data": {"text": " hello"}},
            ],
        }

        self.assertIsNone(extract_group_at_text(event))

    def test_ignores_plain_at_text(self) -> None:
        event = {
            "self_id": 2908229650,
            "message": [{"type": "text", "data": {"text": "@samyyy hello"}}],
        }

        self.assertIsNone(extract_group_at_text(event))

    def test_concatenates_text_segments_after_bot_mention(self) -> None:
        event = {
            "self_id": "2908229650",
            "message": [
                {"type": "at", "data": {"qq": 2908229650}},
                {"type": "text", "data": {"text": " hello"}},
                {"type": "image", "data": {"file": "image.jpg"}},
                {"type": "text", "data": {"text": " world "}},
            ],
        }

        self.assertEqual(extract_group_at_text(event), "hello world")

    def test_returns_empty_text_when_mention_has_no_following_text(self) -> None:
        event = {
            "self_id": 2908229650,
            "message": [{"type": "at", "data": {"qq": "2908229650"}}],
        }

        self.assertEqual(extract_group_at_text(event), "")

    def test_returns_none_without_message_array(self) -> None:
        self.assertIsNone(extract_group_at_text({"self_id": 2908229650}))

    def test_identifies_self_message_with_mixed_id_types(self) -> None:
        self.assertTrue(is_self_message({"self_id": 2908229650, "user_id": "2908229650"}))

    def test_does_not_identify_other_user_as_self(self) -> None:
        self.assertFalse(is_self_message({"self_id": 2908229650, "user_id": 2543642119}))


if __name__ == "__main__":
    unittest.main()
