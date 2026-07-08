from datetime import date

import render

SUMMARY = {
    "overview": "今天 AI 圈发布了多款新模型。",
    "items": [
        {"zh_title": "GPT-5 发布", "zh_summary": "OpenAI 推出 GPT-5。",
         "url": "https://a.com/gpt5", "source": "HackerNews"},
        {"zh_title": "新智能体框架", "zh_summary": "一个开源 agent 框架。",
         "url": "https://b.com/agent", "source": "HackerNews"},
        {"zh_title": "热门仓库", "zh_summary": "当日 star 暴涨。",
         "url": "https://github.com/x/y", "source": "GitHub"},
    ],
}


def test_subject_contains_date_and_count():
    subj = render.subject(count=3, day=date(2026, 7, 8))
    assert "2026-07-08" in subj
    assert "3" in subj


def test_render_html_contains_overview_and_all_items():
    html = render.render_html(SUMMARY)
    assert "今天 AI 圈发布了多款新模型。" in html
    assert "GPT-5 发布" in html
    assert "新智能体框架" in html
    assert "热门仓库" in html
    # 链接可点
    assert 'href="https://a.com/gpt5"' in html
    assert 'href="https://github.com/x/y"' in html


def test_render_html_groups_by_source():
    html = render.render_html(SUMMARY)
    # 两个来源分组标题都出现，且每个只出现一次作为分组标题
    assert "HackerNews" in html
    assert "GitHub" in html
    # HackerNews 分组应在 GitHub 之前（保持首次出现顺序）
    assert html.index("HackerNews") < html.index("GitHub")


def test_render_html_escapes_special_characters():
    summary = {
        "overview": "a < b & c",
        "items": [{"zh_title": "标题 <script>", "zh_summary": "x & y",
                   "url": "https://z.com/1", "source": "RSS"}],
    }
    html = render.render_html(summary)
    assert "<script>" not in html  # 被转义
    assert "&lt;script&gt;" in html


def test_render_text_is_plain_and_has_links():
    text = render.render_text(SUMMARY)
    assert "今天 AI 圈发布了多款新模型。" in text
    assert "GPT-5 发布" in text
    assert "https://a.com/gpt5" in text
    assert "<" not in text  # 纯文本无 HTML 标签


def test_render_text_groups_by_source():
    text = render.render_text(SUMMARY)
    assert "HackerNews" in text
    assert "GitHub" in text
