import json
from datetime import datetime, timezone

import summarizer
from models import Item


def _item(url, title, source="HackerNews", text="raw"):
    return Item(
        title=title, url=url, source=source,
        published_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
        raw_text=text,
    )


class FakeCompletions:
    def __init__(self, content):
        self._content = content
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        message = type("Msg", (), {"content": self._content})()
        choice = type("Choice", (), {"message": message})()
        return type("Resp", (), {"choices": [choice]})()


class FakeClient:
    def __init__(self, content):
        self.chat = type("Chat", (), {"completions": FakeCompletions(content)})()


def test_build_messages_includes_all_items_and_asks_for_json():
    items = [_item("https://a.com/1", "GPT-5 launch"),
             _item("https://b.com/2", "New agent framework")]
    messages = summarizer.build_messages(items)
    joined = json.dumps(messages, ensure_ascii=False)
    assert "GPT-5 launch" in joined
    assert "New agent framework" in joined
    assert "https://a.com/1" in joined
    assert "JSON" in joined or "json" in joined
    assert messages[0]["role"] == "system"


def test_summarize_parses_json_and_returns_structure():
    payload = {
        "overview": "今天 AI 圈很热闹。",
        "items": [
            {"zh_title": "GPT-5 发布", "zh_summary": "摘要一。",
             "url": "https://a.com/1", "source": "HackerNews"},
        ],
    }
    client = FakeClient(json.dumps(payload))
    items = [_item("https://a.com/1", "GPT-5 launch")]
    result = summarizer.summarize(items, client=client, model="qwen-plus")
    assert result["overview"] == "今天 AI 圈很热闹。"
    assert result["items"][0]["zh_title"] == "GPT-5 发布"
    # 确认请求了 JSON 输出格式
    assert client.chat.completions.last_kwargs["response_format"] == {"type": "json_object"}
    assert client.chat.completions.last_kwargs["model"] == "qwen-plus"


def test_summarize_raises_on_invalid_json():
    client = FakeClient("这不是 JSON")
    items = [_item("https://a.com/1", "x")]
    try:
        summarizer.summarize(items, client=client, model="qwen-plus")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_summarize_raises_when_items_key_missing():
    client = FakeClient(json.dumps({"overview": "只有总览"}))
    items = [_item("https://a.com/1", "x")]
    try:
        summarizer.summarize(items, client=client, model="qwen-plus")
        assert False, "expected ValueError"
    except ValueError:
        pass
