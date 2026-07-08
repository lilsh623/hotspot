"""已推送记录的持久化：seen.json 读写、30 天清理、记录已推送 URL。

存储格式：{ 规范化URL: "YYYY-MM-DD" }。日期为该条被推送的日期。
"""

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from sources.base import normalize_url

logger = logging.getLogger(__name__)

_DATE_FMT = "%Y-%m-%d"


def load(path: Path) -> dict[str, str]:
    """读取 seen.json；文件不存在或损坏时返回空 dict。"""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("seen.json 读取失败，按空处理：%s", exc)
        return {}


def save(path: Path, data: dict[str, str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def seen_url_set(data: dict[str, str]) -> set[str]:
    """返回已推送的规范化 URL 集合，供 pipeline 过滤用。"""
    return set(data.keys())


def record(data: dict[str, str], urls: list[str], today: date) -> dict[str, str]:
    """把本次推送的 URL（规范化后）记入一份新 dict 并返回，不修改入参。"""
    updated = dict(data)
    stamp = today.strftime(_DATE_FMT)
    for url in urls:
        updated[normalize_url(url)] = stamp
    return updated


def prune(data: dict[str, str], today: date, days: int = 30) -> dict[str, str]:
    """删除早于 days 天的记录；日期无法解析的条目也删除。"""
    cutoff = today - timedelta(days=days)
    kept: dict[str, str] = {}
    for url, stamp in data.items():
        try:
            pushed = datetime.strptime(stamp, _DATE_FMT).date()
        except (ValueError, TypeError):
            continue
        if pushed >= cutoff:
            kept[url] = stamp
    return kept
