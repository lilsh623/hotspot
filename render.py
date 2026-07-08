"""把 Qwen 的摘要 JSON 渲染成 HTML + 纯文本邮件正文，按来源分组。"""

from datetime import date
from html import escape

_STYLE_BODY = (
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
    "'PingFang SC','Microsoft YaHei',sans-serif;"
    "max-width:680px;margin:0 auto;padding:16px;color:#1a1a1a;"
    "line-height:1.6;"
)


def subject(count: int, day: date) -> str:
    return f"AI 技术热点日报 · {day.isoformat()}（共 {count} 条）"


def _group_by_source(items: list[dict]) -> list[tuple[str, list[dict]]]:
    """按来源分组，保持来源首次出现的顺序。"""
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for item in items:
        src = item.get("source", "其他")
        if src not in groups:
            groups[src] = []
            order.append(src)
        groups[src].append(item)
    return [(src, groups[src]) for src in order]


def render_html(summary: dict) -> str:
    items = summary.get("items", [])
    overview = summary.get("overview", "")
    day = date.today()

    parts = [
        f'<body style="{_STYLE_BODY}">',
        f'<h1 style="font-size:20px;border-bottom:2px solid #eee;padding-bottom:8px;">'
        f'AI 技术热点日报 · {day.isoformat()}</h1>',
        '<div style="background:#f6f8fa;padding:12px 16px;border-radius:8px;'
        f'margin:16px 0;"><strong>今日总览</strong><br>{escape(overview)}</div>',
    ]

    for src, group in _group_by_source(items):
        parts.append(
            f'<h2 style="font-size:16px;color:#0366d6;margin-top:24px;'
            f'border-left:4px solid #0366d6;padding-left:8px;">{escape(src)}</h2>'
        )
        for idx, item in enumerate(group, 1):
            title = escape(item.get("zh_title", ""))
            body = escape(item.get("zh_summary", ""))
            url = escape(item.get("url", ""), quote=True)
            parts.append(
                f'<div style="margin:12px 0;">'
                f'<div style="font-weight:600;">{idx}. {title}</div>'
                f'<div style="color:#444;margin:4px 0;">{body}</div>'
                f'<a href="{url}" style="color:#0366d6;text-decoration:none;">'
                f'🔗 阅读原文</a></div>'
            )

    parts.append(
        f'<hr style="border:none;border-top:1px solid #eee;margin-top:24px;">'
        f'<p style="color:#999;font-size:12px;">共 {len(items)} 条 · '
        f'由 hotspot-github 自动生成</p>'
    )
    parts.append("</body>")
    return "\n".join(parts)


def render_text(summary: dict) -> str:
    items = summary.get("items", [])
    overview = summary.get("overview", "")
    day = date.today()

    lines = [
        f"AI 技术热点日报 · {day.isoformat()}",
        "=" * 40,
        "",
        "【今日总览】",
        overview,
        "",
    ]
    for src, group in _group_by_source(items):
        lines.append(f"── {src} ──")
        for idx, item in enumerate(group, 1):
            lines.append(f"{idx}. {item.get('zh_title', '')}")
            lines.append(f"   {item.get('zh_summary', '')}")
            lines.append(f"   {item.get('url', '')}")
            lines.append("")
    lines.append(f"共 {len(items)} 条 · 由 hotspot-github 自动生成")
    return "\n".join(lines)
