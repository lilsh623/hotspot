import importlib

import config as config_module


def reload_config(monkeypatch, **env):
    for key in [
        "DASHSCOPE_API_KEY", "QWEN_MODEL", "SMTP_HOST", "SMTP_PORT",
        "SMTP_USER", "SMTP_PASS", "MAIL_FROM", "MAIL_TO",
        "ITEMS_PER_SOURCE", "AI_KEYWORDS", "RSS_FEEDS",
    ]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(config_module)


def test_defaults_applied(monkeypatch):
    cfg = reload_config(monkeypatch)
    assert cfg.QWEN_MODEL == "qwen-plus"
    assert cfg.ITEMS_PER_SOURCE == 10
    assert cfg.SMTP_PORT == 465
    assert isinstance(cfg.AI_KEYWORDS, list) and "ai" in cfg.AI_KEYWORDS
    assert isinstance(cfg.RSS_FEEDS, list) and len(cfg.RSS_FEEDS) > 0


def test_env_overrides(monkeypatch):
    cfg = reload_config(
        monkeypatch,
        ITEMS_PER_SOURCE="5",
        QWEN_MODEL="qwen-max",
        AI_KEYWORDS="foo, bar ,baz",
        RSS_FEEDS="https://a.com/feed, https://b.com/feed",
    )
    assert cfg.ITEMS_PER_SOURCE == 5
    assert cfg.QWEN_MODEL == "qwen-max"
    assert cfg.AI_KEYWORDS == ["foo", "bar", "baz"]
    assert cfg.RSS_FEEDS == ["https://a.com/feed", "https://b.com/feed"]


def test_empty_numeric_env_falls_back_to_default(monkeypatch):
    # GitHub Actions vars 若创建但留空，会注入空字符串，不能让 int('') 崩溃
    cfg = reload_config(monkeypatch, ITEMS_PER_SOURCE="", SMTP_PORT="")
    assert cfg.ITEMS_PER_SOURCE == 10
    assert cfg.SMTP_PORT == 465


def test_invalid_numeric_env_falls_back_to_default(monkeypatch):
    cfg = reload_config(monkeypatch, ITEMS_PER_SOURCE="abc")
    assert cfg.ITEMS_PER_SOURCE == 10


def test_require_returns_value_when_set(monkeypatch):
    cfg = reload_config(monkeypatch, DASHSCOPE_API_KEY="sk-123")
    assert cfg.require("DASHSCOPE_API_KEY") == "sk-123"


def test_require_raises_when_missing(monkeypatch):
    cfg = reload_config(monkeypatch)
    try:
        cfg.require("DASHSCOPE_API_KEY")
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "DASHSCOPE_API_KEY" in str(exc)
