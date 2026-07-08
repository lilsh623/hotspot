from datetime import datetime, timezone

from models import Item


def test_item_holds_all_fields():
    now = datetime(2026, 7, 8, tzinfo=timezone.utc)
    item = Item(
        title="GPT-5 released",
        url="https://example.com/gpt5",
        source="HackerNews",
        published_at=now,
        raw_text="details here",
        score=512,
    )
    assert item.title == "GPT-5 released"
    assert item.url == "https://example.com/gpt5"
    assert item.source == "HackerNews"
    assert item.published_at == now
    assert item.raw_text == "details here"
    assert item.score == 512


def test_item_score_and_text_default_to_empty():
    item = Item(
        title="t",
        url="https://example.com/x",
        source="RSS",
        published_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
    )
    assert item.score is None
    assert item.raw_text == ""
