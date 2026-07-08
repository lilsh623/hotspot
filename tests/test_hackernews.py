import sources.hackernews as hn


def test_fetch_filters_ai_and_sorts_by_score(monkeypatch):
    top_ids = [1, 2, 3]
    stories = {
        1: {"title": "New LLM breakthrough", "url": "https://a.com/llm",
             "score": 100, "time": 1751932800, "type": "story"},
        2: {"title": "Best sourdough recipe", "url": "https://b.com/bread",
             "score": 300, "time": 1751932800, "type": "story"},
        3: {"title": "GPT agent framework", "url": "https://c.com/agent",
             "score": 250, "time": 1751932800, "type": "story"},
    }

    def fake_get_json(url):
        if url.endswith("topstories.json"):
            return top_ids
        for sid, story in stories.items():
            if f"item/{sid}.json" in url:
                return story
        return None

    monkeypatch.setattr(hn, "_get_json", fake_get_json)
    monkeypatch.setattr(hn.config, "AI_KEYWORDS", ["llm", "gpt", "agent"])

    items = hn.fetch(limit=10)

    urls = [it.url for it in items]
    assert "https://b.com/bread" not in urls  # 非 AI 被过滤
    assert items[0].url == "https://c.com/agent"  # 250 分排在前
    assert items[1].url == "https://a.com/llm"    # 100 分在后
    assert items[0].source == "HackerNews"
    assert items[0].score == 250


def test_fetch_respects_limit(monkeypatch):
    top_ids = [1, 2]
    stories = {
        1: {"title": "AI one", "url": "https://a.com/1", "score": 50,
             "time": 1751932800, "type": "story"},
        2: {"title": "AI two", "url": "https://a.com/2", "score": 90,
             "time": 1751932800, "type": "story"},
    }

    def fake_get_json(url):
        if url.endswith("topstories.json"):
            return top_ids
        for sid, story in stories.items():
            if f"item/{sid}.json" in url:
                return story
        return None

    monkeypatch.setattr(hn, "_get_json", fake_get_json)
    monkeypatch.setattr(hn.config, "AI_KEYWORDS", ["ai"])

    items = hn.fetch(limit=1)
    assert len(items) == 1
    assert items[0].url == "https://a.com/2"  # 分数更高


def test_fetch_returns_empty_on_network_error(monkeypatch):
    def boom(url):
        raise RuntimeError("network down")

    monkeypatch.setattr(hn, "_get_json", boom)
    assert hn.fetch(limit=5) == []
