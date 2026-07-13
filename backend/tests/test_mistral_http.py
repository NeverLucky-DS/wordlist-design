"""Unit tests for the shared Mistral HTTP helper (429 / Retry-After)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services import mistral_http


def _resp(status: int, content: dict | None = None, retry_after: str | None = None):
    r = MagicMock()
    r.status_code = status
    r.headers = {"Retry-After": retry_after} if retry_after else {}
    if status == 200:
        r.json.return_value = {
            "choices": [{"message": {"content": json.dumps(content or {})}}]
        }
        r.raise_for_status.return_value = None
    else:
        r.raise_for_status.side_effect = Exception(f"HTTP {status}")
    return r


def test_retries_on_429_with_retry_after_then_succeeds():
    responses = [_resp(429, retry_after="0"), _resp(200, {"ok": True})]
    with (
        patch.object(mistral_http._requests, "post", side_effect=responses) as post,
        patch.object(mistral_http.time, "sleep") as sleep,
    ):
        mistral_http._cooldown_until = 0.0
        out = mistral_http.post_mistral_json(
            [{"role": "user", "content": "hi"}], "key", "model", delays=[1, 2],
        )
    assert out == {"ok": True}
    assert post.call_count == 2
    # Retry-After: 0 honoured (not the fallback backoff)
    sleep.assert_called_with(0.0)


def test_raises_after_exhausted_retries():
    responses = [_resp(429), _resp(429), _resp(429)]
    with (
        patch.object(mistral_http._requests, "post", side_effect=responses),
        patch.object(mistral_http.time, "sleep"),
    ):
        mistral_http._cooldown_until = 0.0
        with pytest.raises(Exception):
            mistral_http.post_mistral_json(
                [{"role": "user", "content": "hi"}], "key", "model", delays=[1, 2],
            )


def test_rejects_non_object_json():
    responses = [_resp(200, None)]
    responses[0].json.return_value = {
        "choices": [{"message": {"content": json.dumps([1, 2])}}]
    }
    with patch.object(mistral_http._requests, "post", side_effect=responses):
        mistral_http._cooldown_until = 0.0
        with pytest.raises(ValueError):
            mistral_http.post_mistral_json(
                [{"role": "user", "content": "hi"}], "key", "model",
            )


def test_always_requests_json_object():
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["payload"] = json
        return _resp(200, {"ok": True})

    with patch.object(mistral_http._requests, "post", side_effect=fake_post):
        mistral_http._cooldown_until = 0.0
        mistral_http.post_mistral_json([{"role": "user", "content": "hi"}], "key", "model")

    assert captured["payload"]["response_format"] == {"type": "json_object"}
