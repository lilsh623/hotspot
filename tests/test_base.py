from sources.base import normalize_url, is_ai_relevant


def test_normalize_strips_utm_and_tracking_params():
    url = "https://Example.com/path?utm_source=hn&utm_medium=x&id=42"
    assert normalize_url(url) == "https://example.com/path?id=42"


def test_normalize_removes_trailing_slash():
    assert normalize_url("https://example.com/path/") == "https://example.com/path"


def test_normalize_lowercases_host_only_not_path():
    assert normalize_url("https://Example.COM/Path/To") == "https://example.com/Path/To"


def test_normalize_drops_query_when_all_params_are_tracking():
    assert normalize_url("https://example.com/a?utm_source=x") == "https://example.com/a"


def test_normalize_root_keeps_single_slash():
    assert normalize_url("https://example.com/") == "https://example.com/"


def test_is_ai_relevant_matches_keyword_case_insensitive():
    assert is_ai_relevant("New LLM beats GPT-4", ["llm", "gpt"]) is True
    assert is_ai_relevant("A story about GARDENING", ["llm", "gpt"]) is False


def test_is_ai_relevant_checks_title_and_text():
    assert is_ai_relevant("Cooking tips", ["agent"], text="built an AI agent") is True
