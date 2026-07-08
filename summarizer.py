"""通义千问摘要器：把候选条目交给 Qwen，输出中文总览 + 逐条摘要。

Qwen 只做翻译 + 摘要 + 写总览，不做筛选。强制 JSON 输出。
"""

import json
import logging

from openai import OpenAI

import config
from models import Item

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """你是一名资深 AI 技术编辑。下面会给你一组今日 AI/技术热点条目（标题可能是英文）。

你的任务：
1. 为每一条生成简洁的中文标题，以及 2-3 句客观的中文摘要。
2. 摘要要客观、不夸大，保留关键的数字、模型名、公司名等事实信息。
3. 另写一段 3-5 句的当日整体中文总览，概括今天 AI/技术圈发生了什么。
4. 保持条目的输入顺序，不要增删条目，不要改动 url 和 source 字段。

严格按如下 JSON 格式输出，不要输出任何多余文字：
{
  "overview": "当日整体中文总览……",
  "items": [
    {"zh_title": "中文标题", "zh_summary": "中文摘要", "url": "原始url", "source": "原始source"}
  ]
}"""


def build_messages(items: list[Item]) -> list[dict]:
    """构造发给 Qwen 的 messages。用户消息内嵌所有候选条目。"""
    payload = [
        {
            "index": i,
            "title": it.title,
            "source": it.source,
            "url": it.url,
            "text": (it.raw_text or "")[:800],
        }
        for i, it in enumerate(items)
    ]
    user_content = (
        "以下是今日候选热点条目（JSON 数组），请按系统指令处理并输出 JSON：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def make_client() -> OpenAI:
    """用配置构造 Qwen 的 OpenAI 兼容客户端。"""
    return OpenAI(
        api_key=config.require("DASHSCOPE_API_KEY"),
        base_url=config.QWEN_BASE_URL,
    )


def summarize(items: list[Item], client: OpenAI, model: str) -> dict:
    """调用 Qwen 生成摘要，返回 {overview, items}。解析失败抛 ValueError。"""
    messages = build_messages(items)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Qwen 返回的不是合法 JSON：{exc}") from exc

    if not isinstance(data, dict) or "items" not in data or "overview" not in data:
        raise ValueError("Qwen 返回缺少 overview 或 items 字段")
    return data
