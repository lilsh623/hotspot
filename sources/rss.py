"""RSS/官方博客抓取器：feedparser 解析，按发布时间取最新。

RSS 源本身即为 AI 官方博客/arXiv，不做关键词初筛。
"""

import logging
import time
from datetime import datetime, timezone

import feedparser

import config
from models import Item

logger = logging.getLogger(__name__)


def _to_datetime(entry) -> datetime:
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if struct:
        return datetime.fromtimestamp(time.mktime(struct), tz=timezone.utc)
    return datetime.now(timezone.utc)


def fetch(limit: int) -> list[Item]:
    items: list[Item] = []
    for feed_url in config.RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.warning("RSS 解析失败 %s：%s", feed_url, exc)
            continue
        for entry in getattr(parsed, "entries", []):
            link = entry.get("link")
            if not link:
                continue
            items.append(Item(
                title=entry.get("title", ""),
                url=link,
                source="RSS",
                published_at=_to_datetime(entry),
                raw_text=entry.get("summary", ""),
                score=None,
            ))

    items.sort(key=lambda it: it.published_at, reverse=True)
    return items[:limit]
