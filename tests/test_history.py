"""Tests for push2talk.history module."""

from __future__ import annotations

import threading

from push2talk.history import RecognitionHistory


def test_add_and_get_single():
    h = RecognitionHistory()
    h.add("hello")
    assert h.get_items() == ["hello"]


def test_add_ordering_newest_first():
    h = RecognitionHistory()
    h.add("first")
    h.add("second")
    h.add("third")
    items = h.get_items()
    assert items[0] == "third"
    assert items[1] == "second"
    assert items[2] == "first"


def test_maxlen_enforced():
    h = RecognitionHistory(maxlen=3)
    for i in range(5):
        h.add(str(i))
    items = h.get_items()
    assert len(items) == 3
    # newest items survive
    assert "4" in items
    assert "3" in items
    assert "2" in items


def test_clear():
    h = RecognitionHistory()
    h.add("a")
    h.add("b")
    h.clear()
    assert h.get_items() == []


def test_get_items_returns_copy():
    h = RecognitionHistory()
    h.add("x")
    items = h.get_items()
    items.append("injected")
    assert "injected" not in h.get_items()


def test_thread_safety():
    h = RecognitionHistory(maxlen=100)
    errors = []

    def worker(prefix: str):
        try:
            for i in range(20):
                h.add(f"{prefix}-{i}")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    # 5 threads × 20 items = 100, maxlen=100 so all fit
    assert len(h.get_items()) == 100


def test_empty_history_returns_empty_list():
    h = RecognitionHistory()
    assert h.get_items() == []


def test_default_maxlen():
    h = RecognitionHistory()
    for i in range(15):
        h.add(str(i))
    # default maxlen=10
    assert len(h.get_items()) == 10
