from typing import Optional

import pytest

from notion_exporter.block_converter import BlockConverter


def callout_block(icon: Optional[dict]) -> dict:
    return {
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "Watch out!", "link": None},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                    "plain_text": "Watch out!",
                    "href": None,
                }
            ],
            "icon": icon,
        },
    }


class TestCallout:
    def test_emoji_icon(self):
        block = callout_block({"type": "emoji", "emoji": "⚠️"})
        assert BlockConverter.callout(block) == "⚠️ Watch out!"

    def test_no_icon(self):
        # Notion returns `"icon": null` for callouts without an icon.
        block = callout_block(None)
        assert BlockConverter.callout(block) == "Watch out!"

    def test_missing_icon_key(self):
        block = callout_block(None)
        del block["callout"]["icon"]
        assert BlockConverter.callout(block) == "Watch out!"

    @pytest.mark.parametrize(
        "icon",
        [
            {"type": "external", "external": {"url": "https://example.com/icon.png"}},
            {"type": "file", "file": {"url": "https://example.com/icon.png", "expiry_time": "2024-01-01T00:00:00.000Z"}},
        ],
    )
    def test_image_icon_is_skipped(self, icon):
        block = callout_block(icon)
        assert BlockConverter.callout(block) == "Watch out!"

    def test_convert_block_dispatches_iconless_callout(self):
        assert BlockConverter().convert_block(callout_block(None)) == "Watch out!"
