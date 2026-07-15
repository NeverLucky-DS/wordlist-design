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
        mistral_http._cooldowns.clear()
        out = mistral_http.post_mistral_json(
            [{"role": "user", "content": "hi"}], "key", "model", delays=[1, 2],
        )
    assert out == {"ok": True}
    assert post.call_count == 2
    # Retry-After: 0 honoured (not the fallback backoff)
    sleep.assert_called_with(0.0)


def test_retries_on_connection_drop_then_succeeds():
    """A dropped connection (RemoteDisconnected) must be retried, not fatal."""
    drop = mistral_http._requests.exceptions.ConnectionError("Remote end closed")
    with (
        patch.object(
            mistral_http._requests, "post",
            side_effect=[drop, _resp(200, {"ok": True})],
        ) as post,
        patch.object(mistral_http.time, "sleep") as sleep,
    ):
        mistral_http._cooldowns.clear()
        out = mistral_http.post_mistral_json(
            [{"role": "user", "content": "hi"}], "key", "model", delays=[3, 5],
        )
    assert out == {"ok": True}
    assert post.call_count == 2
    sleep.assert_called_once_with(3.0)


def test_reraises_connection_drop_after_exhausted_retries():
    drop = mistral_http._requests.exceptions.ConnectionError("Remote end closed")
    with (
        patch.object(mistral_http._requests, "post", side_effect=[drop, drop, drop]),
        patch.object(mistral_http.time, "sleep"),
    ):
        mistral_http._cooldowns.clear()
        with pytest.raises(mistral_http._requests.exceptions.ConnectionError):
            mistral_http.post_mistral_json(
                [{"role": "user", "content": "hi"}], "key", "model", delays=[1, 2],
            )


def test_retries_on_500_then_succeeds():
    with (
        patch.object(
            mistral_http._requests, "post",
            side_effect=[_resp(500), _resp(200, {"ok": True})],
        ) as post,
        patch.object(mistral_http.time, "sleep") as sleep,
    ):
        mistral_http._cooldowns.clear()
        out = mistral_http.post_mistral_json(
            [{"role": "user", "content": "hi"}], "key", "model", delays=[2, 4],
        )
    assert out == {"ok": True}
    assert post.call_count == 2
    sleep.assert_called_once_with(2.0)


def test_cooldown_is_per_key():
    """A 429 on one key must not stall a different key."""
    mistral_http._cooldowns.clear()
    mistral_http._set_cooldown("key-a", 100.0)
    with mistral_http._cooldown_lock:
        assert mistral_http._cooldowns.get(mistral_http._key_id("key-a"), 0) > 0
        assert mistral_http._cooldowns.get(mistral_http._key_id("key-b"), 0) == 0


def test_cooldown_dict_holds_no_raw_keys():
    """Cooldown must not retain the raw secret as a dict key."""
    mistral_http._cooldowns.clear()
    secret = "sk-super-secret-value"
    mistral_http._set_cooldown(secret, 100.0)
    assert secret not in mistral_http._cooldowns
    assert mistral_http._key_id(secret) in mistral_http._cooldowns


def test_raises_after_exhausted_retries():
    responses = [_resp(429), _resp(429), _resp(429)]
    with (
        patch.object(mistral_http._requests, "post", side_effect=responses),
        patch.object(mistral_http.time, "sleep"),
    ):
        mistral_http._cooldowns.clear()
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
        mistral_http._cooldowns.clear()
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
        mistral_http._cooldowns.clear()
        mistral_http.post_mistral_json([{"role": "user", "content": "hi"}], "key", "model")

    assert captured["payload"]["response_format"] == {"type": "json_object"}
