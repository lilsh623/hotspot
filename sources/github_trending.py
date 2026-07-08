"""GitHub Trending 抓取器：HTML 解析（无官方 API），按当日 star 排序。

风险：GitHub 页面改版时选择器可能失效，需偶尔维护。
"""

import logging
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

import config
from models import Item
from sources.base import is_ai_relevant

logger = logging.getLogger(__name__)

_TRENDING_URL = "https://github.com/trending?since=daily"
_STARS_TODAY = re.compile(r"([\d,]+)\s+stars?\s+today")


def _get_html(url: str) -> str:
    resp = requests.get(
        url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (hotspot-github)"}
    )
    resp.raise_for_status()
    return resp.text


def _parse_stars(text: str) -> int | None:
    match = _STARS_TODAY.search(text or "")
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def fetch(limit: int) -> list[Item]:
    try:
        html = _get_html(_TRENDING_URL)
    except Exception as exc:
        logger.warning("GitHub Trending 获取失败：%s", exc)
        return []

    now = datetime.now(timezone.utc)
    items: list[Item] = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for article in soup.select("article.Box-row"):
            link = article.select_one("h2 a")
            if not link or not link.get("href"):
                continue
            repo_path = link["href"].strip("/")
            desc_el = article.select_one("p")
            description = desc_el.get_text(strip=True) if desc_el else ""
            stars = _parse_stars(article.get_text(" "))

            if not is_ai_relevant(repo_path, config.AI_KEYWORDS, text=description):
                continue

            items.append(Item(
                title=repo_path,
                url=f"https://github.com/{repo_path}",
                source="GitHub",
                published_at=now,
                raw_text=description,
                score=stars,
            ))
    except Exception as exc:
        logger.warning("GitHub Trending 解析失败：%s", exc)
        return []

    items.sort(key=lambda it: it.score or 0, reverse=True)
    return items[:limit]
