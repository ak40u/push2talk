"""Tests for push2talk.inserter module."""

from __future__ import annotations

from unittest.mock import call, patch


def test_empty_text_is_noop(mock_pyperclip, mock_keyboard):
    from push2talk.inserter import insert_text
    insert_text("")
    mock_pyperclip.copy.assert_not_called()
    mock_keyboard.send.assert_not_called()


def test_insert_copies_to_clipboard(mock_pyperclip, mock_keyboard):
    with patch("push2talk.inserter.time.sleep"):
        from push2talk.inserter import insert_text
        insert_text("hello")
    mock_pyperclip.copy.assert_any_call("hello")


def test_insert_sends_ctrl_v(mock_pyperclip, mock_keyboard):
    mock_keyboard.send.reset_mock()
    with patch("push2talk.inserter.time.sleep"):
        from push2talk.inserter import insert_text
        insert_text("hello")
    # keyboard.send should have been called with "ctrl+v"
    calls = [c.args[0] for c in mock_keyboard.send.call_args_list if c.args]
    assert "ctrl+v" in calls


def test_clipboard_restored_after_paste(mock_pyperclip, mock_keyboard):
    mock_pyperclip.paste.return_value = "previous content"
    with patch("push2talk.inserter.time.sleep"):
        from push2talk.inserter import insert_text
        insert_text("new text")
    # Last copy call should restore previous clipboard
    last_copy_call = mock_pyperclip.copy.call_args_list[-1]
    assert last_copy_call == call("previous content")


def test_clipboard_not_restored_when_paste_fails(mock_pyperclip, mock_keyboard):
    """If paste() raises, prev=None, no restore copy after ctrl+v."""
    mock_pyperclip.paste.side_effect = Exception("clipboard error")
    mock_pyperclip.copy.reset_mock()

    with patch("push2talk.inserter.time.sleep"):
        from push2talk.inserter import insert_text
        insert_text("text")

    # Only one copy call: the text itself (no restore)
    assert mock_pyperclip.copy.call_count == 1
    assert mock_pyperclip.copy.call_args == call("text")


def test_none_prev_clipboard_no_restore(mock_pyperclip, mock_keyboard):
    """When prev clipboard is empty string, restore still happens."""
    mock_pyperclip.paste.return_value = ""
    with patch("push2talk.inserter.time.sleep"):
        from push2talk.inserter import insert_text
        insert_text("something")
    # paste returned "", which is not None, so restore should occur
    calls = [c[0][0] for c in mock_pyperclip.copy.call_args_list]
    assert "something" in calls
    assert "" in calls
