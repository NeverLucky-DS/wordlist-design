"""Additional Mistral HTTP edge cases and cooldown behaviour."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services import mistral_http


def _ok(content: dict):
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status.return_value = None
    r.json.return_value = {
        "choices": [{"message": {"content": json.dumps(content)}}]
    }
    return r


def test_cooldown_blocks_immediate_second_call():
    calls = []

    def fake_post(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            r = MagicMock()
            r.status_code = 429
            r.headers = {"Retry-After": "1"}
            r.raise_for_status.side_effect = Exception("429")
            return r
        return _ok({"v": 2})

    with (
        patch.object(mistral_http._requests, "post", side_effect=fake_post),
        patch.object(mistral_http.time, "sleep") as sleep,
        patch.object(mistral_http.time, "monotonic", side_effect=[0.0, 0.0, 2.0, 2.0, 2.0]),
    ):
        mistral_http._cooldowns.clear()
        out = mistral_http.post_mistral_json(
            [{"role": "user", "content": "x"}], "key", "model", delays=[1]
        )
    assert out == {"v": 2}
    assert sleep.call_count >= 1


def test_passes_temperature_to_api():
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["json"] = json
        return _ok({})

    with patch.object(mistral_http._requests, "post", side_effect=fake_post):
        mistral_http._cooldowns.clear()
        mistral_http.post_mistral_json(
            [{"role": "user", "content": "hi"}],
            "key",
            "model",
            temperature=0.4,
        )
    assert captured["json"]["temperature"] == 0.4


def test_invalid_retry_after_falls_back_to_delay():
    r429 = MagicMock()
    r429.status_code = 429
    r429.headers = {"Retry-After": "not-a-number"}
    r429.raise_for_status.side_effect = Exception("429")

    with (
        patch.object(
            mistral_http._requests,
            "post",
            side_effect=[r429, _ok({"ok": True})],
        ),
        patch.object(mistral_http.time, "sleep") as sleep,
    ):
        mistral_http._cooldowns.clear()
        out = mistral_http.post_mistral_json(
            [{"role": "user", "content": "hi"}], "key", "model", delays=[7]
        )
    assert out == {"ok": True}
    assert sleep.call_count >= 1
    assert sleep.call_args_list[0].args[0] == 7.0
