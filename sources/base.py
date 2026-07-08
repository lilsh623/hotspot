"""抓取器通用工具：URL 规范化与 AI 相关性初筛。

每个抓取器实现同一个接口：模块级 fetch(limit: int) -> list[Item]。
失败时应在内部捕获异常、记日志、返回空列表，绝不向上抛出。
"""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

_TRACKING_PREFIXES = ("utm_",)
_TRACKING_KEYS = {"fbclid", "gclid", "ref", "ref_src", "spm"}


def _is_tracking_param(key: str) -> bool:
    if key in _TRACKING_KEYS:
        return True
    return any(key.startswith(prefix) for prefix in _TRACKING_PREFIXES)


def normalize_url(url: str) -> str:
    """规范化 URL 作为去重主键：小写域名、去追踪参数、去尾部斜杠。"""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()

    kept = [(k, v) for k, v in parse_qsl(parsed.query) if not _is_tracking_param(k)]
    query = urlencode(kept)

    path = parsed.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    return urlunparse((parsed.scheme, netloc, path, parsed.params, query, ""))


def is_ai_relevant(title: str, keywords: list[str], text: str = "") -> bool:
    """标题或正文命中任一关键词（大小写不敏感）即视为 AI 相关。"""
    haystack = f"{title} {text}".lower()
    return any(kw.lower() in haystack for kw in keywords)
