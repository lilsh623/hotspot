from datetime import datetime, timezone

import pipeline
from models import Item


def _item(url, source="HackerNews", score=1):
    return Item(
        title=f"title-{url}",
        url=url,
        source=source,
        published_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
        score=score,
    )


def test_gather_runs_all_fetchers_and_concatenates():
    fake_a = type("M", (), {"fetch": staticmethod(lambda limit: [_item("https://a.com/1")])})
    fake_b = type("M", (), {"fetch": staticmethod(lambda limit: [_item("https://b.com/1")])})
    items = pipeline.gather([fake_a, fake_b], limit=10)
    assert {it.url for it in items} == {"https://a.com/1", "https://b.com/1"}


def test_gather_isolates_a_failing_fetcher():
    def boom(limit):
        raise RuntimeError("fetcher crashed")
    good = type("M", (), {"fetch": staticmethod(lambda limit: [_item("https://ok.com/1")])})
    bad = type("M", (), {"fetch": staticmethod(boom)})
    items = pipeline.gather([bad, good], limit=10)
    assert [it.url for it in items] == ["https://ok.com/1"]


def test_dedupe_removes_within_batch_duplicates_by_normalized_url():
    items = [
        _item("https://example.com/post?utm_source=hn", score=10),
        _item("https://example.com/post/", score=5),  # 规范化后同一条
        _item("https://other.com/x", score=1),
    ]
    result = pipeline.dedupe_and_filter(items, seen_urls=set())
    urls = [it.url for it in result]
    assert len(result) == 2
    # 保留首次出现的那条
    assert "https://example.com/post?utm_source=hn" in urls
    assert "https://other.com/x" in urls


def test_dedupe_drops_already_seen_urls():
    from sources.base import normalize_url
    items = [
        _item("https://example.com/seen"),
        _item("https://example.com/fresh"),
    ]
    seen = {normalize_url("https://example.com/seen")}
    result = pipeline.dedupe_and_filter(items, seen_urls=seen)
    assert [it.url for it in result] == ["https://example.com/fresh"]


def test_dedupe_seen_match_ignores_tracking_params():
    from sources.base import normalize_url
    items = [_item("https://example.com/a?utm_medium=email")]
    seen = {normalize_url("https://example.com/a")}
    assert pipeline.dedupe_and_filter(items, seen_urls=seen) == []
