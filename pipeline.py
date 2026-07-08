"""编排层：运行所有抓取器 → 同批去重 → 剔除已推送。"""

import logging

from models import Item
from sources.base import normalize_url

logger = logging.getLogger(__name__)


def gather(fetchers, limit: int) -> list[Item]:
    """依次运行每个抓取器，单个失败跳过，合并所有结果。"""
    items: list[Item] = []
    for fetcher in fetchers:
        name = getattr(fetcher, "__name__", str(fetcher))
        try:
            fetched = fetcher.fetch(limit)
            logger.info("%s 抓取到 %d 条", name, len(fetched))
            items.extend(fetched)
        except Exception as exc:
            logger.warning("%s 抓取失败：%s", name, exc)
    return items


def dedupe_and_filter(items: list[Item], seen_urls: set[str]) -> list[Item]:
    """按规范化 URL 去重（同批内）并剔除 seen_urls 中已推送的。

    seen_urls 中的元素应为已规范化的 URL。保留每个 URL 首次出现的条目。
    """
    result: list[Item] = []
    batch_seen: set[str] = set()
    for item in items:
        key = normalize_url(item.url)
        if key in seen_urls or key in batch_seen:
            continue
        batch_seen.add(key)
        result.append(item)
    return result
