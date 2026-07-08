from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Item:
    """一条热点条目，贯穿抓取→去重→摘要全流程的统一数据结构。"""

    title: str
    url: str
    source: str
    published_at: datetime
    raw_text: str = ""
    score: int | None = None
