"""抓取器注册表。加新源 = 新增一个文件 + 在 FETCHERS 里注册一行。

每个抓取器暴露模块级 fetch(limit: int) -> list[Item]。
"""

from sources import github_trending, hackernews, rss

FETCHERS = [hackernews, github_trending, rss]
