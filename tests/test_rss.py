import time

import sources.rss as rss


def _entry(title, link, published_struct, summary=""):
    return {
        "title": title,
        "link": link,
        "summary": summary,
        "published_parsed": published_struct,
    }


def test_fetch_maps_entries_to_items_newest_first(monkeypatch):
    older = time.struct_time((2026, 7, 1, 0, 0, 0, 0, 0, 0))
    newer = time.struct_time((2026, 7, 7, 0, 0, 0, 0, 0, 0))

    feeds = {
        "https://feed-a.com/rss": [
            _entry("Old post", "https://a.com/old", older, "old summary"),
            _entry("New post", "https://a.com/new", newer, "new summary"),
        ],
    }

    def fake_parse(url):
        return type("Parsed", (), {"entries": feeds.get(url, [])})()

    monkeypatch.setattr(rss.feedparser, "parse", fake_parse)
    monkeypatch.setattr(rss.config, "RSS_FEEDS", ["https://feed-a.com/rss"])

    items = rss.fetch(limit=10)

    assert items[0].url == "https://a.com/new"  # 最新在前
    assert items[1].url == "https://a.com/old"
    assert items[0].source == "RSS"
    assert items[0].raw_text == "new summary"


def test_fetch_respects_limit_across_feeds(monkeypatch):
    t = time.struct_time((2026, 7, 7, 0, 0, 0, 0, 0, 0))
    feeds = {
        "https://feed-a.com/rss": [_entry("A", "https://a.com/1", t)],
        "https://feed-b.com/rss": [_entry("B", "https://b.com/1", t)],
    }
    monkeypatch.setattr(
        rss.feedparser, "parse",
        lambda url: type("P", (), {"entries": feeds.get(url, [])})(),
    )
    monkeypatch.setattr(
        rss.config, "RSS_FEEDS",
        ["https://feed-a.com/rss", "https://feed-b.com/rss"],
    )
    items = rss.fetch(limit=1)
    assert len(items) == 1


def test_fetch_skips_broken_feed_but_keeps_others(monkeypatch):
    t = time.struct_time((2026, 7, 7, 0, 0, 0, 0, 0, 0))

    def fake_parse(url):
        if "broken" in url:
            raise RuntimeError("bad feed")
        return type("P", (), {"entries": [_entry("Good", "https://g.com/1", t)]})()

    monkeypatch.setattr(rss.feedparser, "parse", fake_parse)
    monkeypatch.setattr(
        rss.config, "RSS_FEEDS",
        ["https://broken.com/rss", "https://good.com/rss"],
    )
    items = rss.fetch(limit=10)
    assert len(items) == 1
    assert items[0].url == "https://g.com/1"
