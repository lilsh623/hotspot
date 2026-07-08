import sources.github_trending as gh

# 精简版 GitHub Trending 页面结构（article.Box-row + 当日 star）
SAMPLE_HTML = """
<html><body>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/acme/llm-toolkit">acme / llm-toolkit</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">A powerful LLM agent framework</p>
  <span class="d-inline-block float-sm-right">1,234 stars today</span>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/foo/garden-planner">foo / garden-planner</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">Plan your vegetable garden</p>
  <span class="d-inline-block float-sm-right">50 stars today</span>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/bar/gpt-tools">bar / gpt-tools</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">Utilities for GPT models</p>
  <span class="d-inline-block float-sm-right">800 stars today</span>
</article>
</body></html>
"""


def test_fetch_parses_repos_filters_ai_sorts_by_stars(monkeypatch):
    monkeypatch.setattr(gh, "_get_html", lambda url: SAMPLE_HTML)
    monkeypatch.setattr(gh.config, "AI_KEYWORDS", ["llm", "gpt", "agent"])

    items = gh.fetch(limit=10)

    urls = [it.url for it in items]
    assert "https://github.com/foo/garden-planner" not in urls  # 非 AI 过滤
    assert items[0].url == "https://github.com/acme/llm-toolkit"  # 1234 star 第一
    assert items[1].url == "https://github.com/bar/gpt-tools"     # 800 star 第二
    assert items[0].source == "GitHub"
    assert items[0].score == 1234
    assert "llm-toolkit" in items[0].title.lower()


def test_fetch_respects_limit(monkeypatch):
    monkeypatch.setattr(gh, "_get_html", lambda url: SAMPLE_HTML)
    monkeypatch.setattr(gh.config, "AI_KEYWORDS", ["llm", "gpt"])
    items = gh.fetch(limit=1)
    assert len(items) == 1
    assert items[0].score == 1234


def test_fetch_returns_empty_on_error(monkeypatch):
    def boom(url):
        raise RuntimeError("boom")
    monkeypatch.setattr(gh, "_get_html", boom)
    assert gh.fetch(limit=5) == []
