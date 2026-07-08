"""Hacker News 抓取器：官方 Firebase API，按分数排序，AI 关键词初筛。"""

import logging
from datetime import datetime, timezone

import requests

import config
from models import Item
from sources.base import is_ai_relevant

logger = logging.getLogger(__name__)

_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
_SCAN_LIMIT = 100  # 最多扫描前 100 条 top stories 做关键词过滤


def _get_json(url: str):
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch(limit: int) -> list[Item]:
    try:
        top_ids = _get_json(_TOP_STORIES) or []
    except Exception as exc:
        logger.warning("HackerNews 获取 topstories 失败：%s", exc)
        return []

    items: list[Item] = []
    for story_id in top_ids[:_SCAN_LIMIT]:
        try:
            story = _get_json(_ITEM.format(id=story_id))
        except Exception as exc:
            logger.warning("HackerNews 获取 item %s 失败：%s", story_id, exc)
            continue
        if not story or story.get("type") != "story":
            continue
        title = story.get("title", "")
        url = story.get("url")
        if not url:
            continue
        if not is_ai_relevant(title, config.AI_KEYWORDS):
            continue
        published = datetime.fromtimestamp(
            story.get("time", 0), tz=timezone.utc
        )
        items.append(Item(
            title=title,
            url=url,
            source="HackerNews",
            published_at=published,
            raw_text="",
            score=story.get("score"),
        ))

    items.sort(key=lambda it: it.score or 0, reverse=True)
    return items[:limit]
