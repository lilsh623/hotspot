import json
from datetime import date

import state


def test_load_returns_empty_dict_when_file_missing(tmp_path):
    assert state.load(tmp_path / "nope.json") == {}


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "seen.json"
    data = {"https://a.com/x": "2026-07-08"}
    state.save(path, data)
    assert state.load(path) == data


def test_load_returns_empty_on_corrupt_file(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text("{ not valid json", encoding="utf-8")
    assert state.load(path) == {}


def test_seen_url_set_returns_keys():
    data = {"https://a.com/x": "2026-07-08", "https://b.com/y": "2026-07-01"}
    assert state.seen_url_set(data) == {"https://a.com/x", "https://b.com/y"}


def test_record_adds_normalized_urls_with_date():
    data = {}
    result = state.record(
        data,
        ["https://Example.com/post/?utm_source=x"],
        today=date(2026, 7, 8),
    )
    assert result == {"https://example.com/post": "2026-07-08"}


def test_record_does_not_mutate_input():
    data = {"https://old.com/1": "2026-07-01"}
    state.record(data, ["https://new.com/2"], today=date(2026, 7, 8))
    assert data == {"https://old.com/1": "2026-07-01"}  # 原对象不变


def test_prune_removes_entries_older_than_30_days():
    data = {
        "https://keep.com/1": "2026-07-01",   # 7 天前，保留
        "https://drop.com/2": "2026-05-01",   # 68 天前，删除
        "https://edge.com/3": "2026-06-08",   # 恰好 30 天前，保留
    }
    result = state.prune(data, today=date(2026, 7, 8), days=30)
    assert set(result.keys()) == {"https://keep.com/1", "https://edge.com/3"}


def test_prune_drops_entries_with_bad_date():
    data = {"https://bad.com/1": "not-a-date", "https://ok.com/2": "2026-07-07"}
    result = state.prune(data, today=date(2026, 7, 8), days=30)
    assert set(result.keys()) == {"https://ok.com/2"}
