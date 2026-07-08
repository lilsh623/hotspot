"""集中读取环境变量配置。密钥类用 require() 在缺失时报错。"""

import os

DEFAULT_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "agent", "model",
    "diffusion", "transformer", "neural", "machine learning", "ml",
    "deep learning", "openai", "anthropic", "claude", "gemini", "llama",
    "rag", "multimodal", "inference", "fine-tune", "embedding",
]

DEFAULT_RSS_FEEDS = [
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://blog.google/technology/ai/rss/",
    "https://huggingface.co/blog/feed.xml",
]


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
ITEMS_PER_SOURCE = int(os.getenv("ITEMS_PER_SOURCE", "10"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MAIL_FROM = os.getenv("MAIL_FROM", "")
MAIL_TO = os.getenv("MAIL_TO", "")

_keywords_env = os.getenv("AI_KEYWORDS", "")
AI_KEYWORDS = _split(_keywords_env) if _keywords_env else list(DEFAULT_KEYWORDS)

_feeds_env = os.getenv("RSS_FEEDS", "")
RSS_FEEDS = _split(_feeds_env) if _feeds_env else list(DEFAULT_RSS_FEEDS)

QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def require(name: str) -> str:
    """读取必填环境变量，缺失或为空时抛 RuntimeError。"""
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"缺少必填环境变量：{name}")
    return value
