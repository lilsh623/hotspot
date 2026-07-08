from datetime import date, datetime, timezone

import main
from models import Item


def _item(url, source="HackerNews"):
    return Item(title=f"t-{url}", url=url, source=source,
                published_at=datetime(2026, 7, 8, tzinfo=timezone.utc))


class Spy:
    """记录 summarize / send / save 是否被调用及参数。"""
    def __init__(self):
        self.summarize_called = False
        self.send_called = False
        self.saved = None

    def summarize(self, items):
        self.summarize_called = True
        return {
            "overview": "总览",
            "items": [{"zh_title": "标题", "zh_summary": "摘要",
                       "url": it.url, "source": it.source} for it in items],
        }

    def send(self, subject, html, text):
        self.send_called = True

    def save_state(self, data):
        self.saved = data


def _run(spy, fetched_items, seen_state, send_error=None, day=date(2026, 7, 8)):
    def send(subject, html, text):
        spy.send(subject, html, text)
        if send_error:
            raise send_error
    return main.run(
        fetchers=[type("M", (), {"fetch": staticmethod(lambda limit: fetched_items)})],
        items_per_source=10,
        load_state=lambda: dict(seen_state),
        summarize=spy.summarize,
        send=send,
        save_state=spy.save_state,
        today=day,
    )


def test_empty_candidates_skips_send_and_state():
    spy = Spy()
    result = _run(spy, fetched_items=[], seen_state={})
    assert spy.summarize_called is False
    assert spy.send_called is False
    assert spy.saved is None
    assert result == 0  # 无内容也算正常退出


def test_all_candidates_already_seen_skips_send():
    from sources.base import normalize_url
    spy = Spy()
    items = [_item("https://a.com/1")]
    seen = {normalize_url("https://a.com/1"): "2026-07-07"}
    _run(spy, fetched_items=items, seen_state=seen)
    assert spy.send_called is False
    assert spy.saved is None


def test_happy_path_sends_and_writes_state():
    spy = Spy()
    items = [_item("https://a.com/1"), _item("https://b.com/2")]
    result = _run(spy, fetched_items=items, seen_state={})
    assert spy.summarize_called is True
    assert spy.send_called is True
    # 状态里应包含两条推送记录，日期为今天
    from sources.base import normalize_url
    assert spy.saved[normalize_url("https://a.com/1")] == "2026-07-08"
    assert spy.saved[normalize_url("https://b.com/2")] == "2026-07-08"
    assert result == 0


def test_send_failure_does_not_write_state():
    spy = Spy()
    items = [_item("https://a.com/1")]
    try:
        _run(spy, fetched_items=items, seen_state={},
             send_error=RuntimeError("smtp down"))
        assert False, "expected error to propagate"
    except RuntimeError:
        pass
    assert spy.saved is None  # 发送失败绝不写状态


def test_state_is_pruned_on_save():
    spy = Spy()
    items = [_item("https://new.com/1")]
    # 一条 68 天前的旧记录应被清理掉
    seen = {"https://old.com/x": "2026-05-01"}
    _run(spy, fetched_items=items, seen_state=seen, day=date(2026, 7, 8))
    assert "https://old.com/x" not in spy.saved
    from sources.base import normalize_url
    assert normalize_url("https://new.com/1") in spy.saved
