"""The gate on POST /api/vocab/enrich/requeue.

`enrich.requeue` defaults to `drop_card=True`: the card leaves `cards` at once,
before any re-enrichment can bring it back. Until 2026-07-26 the route accepted
an arbitrary `lemmas` list from any logged-in account, and signup is open with no
e-mail confirmation — so one registered stranger could post 92 000 lemmas and
empty the dictionary. No page has ever sent that field; the panel's button sends
`scope="low_confidence"` and nothing else.

A length cap would not have closed it (chunk the list and repeat), so the split
is by scope: the bounded scope stays open to any operator, the explicit list is
admin only.
"""

from __future__ import annotations

import pytest

ADMIN_EMAIL = "regular@example.com"   # the non_admin_client fixture's account


@pytest.fixture(autouse=True)
def _isolate_enrich(monkeypatch, tmp_path):
    """Never let a test reach the real enrichment.db."""
    from app.vocab import enrich

    monkeypatch.setattr(enrich, "ENRICH_DB", tmp_path / "enrichment.db")
    monkeypatch.setattr(enrich, "VOCAB_DB", tmp_path / "vocab.db")

    dropped: list[list[str]] = []
    monkeypatch.setattr(enrich, "requeue",
                        lambda lemmas, **kw: (dropped.append(list(lemmas)), len(lemmas))[1])
    monkeypatch.setattr(enrich, "requeue_low_confidence", lambda: 7)
    return dropped


def _as_admin(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", ADMIN_EMAIL)


async def test_explicit_lemma_list_is_closed_to_non_admins(
        non_admin_client, monkeypatch, _isolate_enrich):
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "someone-else@example.com")
    r = await non_admin_client.post("/api/vocab/enrich/requeue",
                                    json={"lemmas": ["Haus", "Wirkung"]})
    assert r.status_code == 403
    assert _isolate_enrich == [], "not one card may be dropped for a non-admin"


async def test_explicit_lemma_list_is_closed_to_guests(
        guest_client, monkeypatch, _isolate_enrich):
    _as_admin(monkeypatch)
    r = await guest_client.post("/api/vocab/enrich/requeue",
                                json={"lemmas": ["Haus"]})
    assert r.status_code == 401
    assert _isolate_enrich == []


async def test_admin_may_still_requeue_an_explicit_list(
        non_admin_client, monkeypatch, _isolate_enrich):
    _as_admin(monkeypatch)
    r = await non_admin_client.post("/api/vocab/enrich/requeue",
                                    json={"lemmas": [" Haus ", "", "Wirkung"]})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "requeued": 2}
    assert _isolate_enrich == [["Haus", "Wirkung"]], "blanks must still be dropped"


async def test_low_confidence_scope_stays_open_to_any_operator(
        non_admin_client, monkeypatch, _isolate_enrich):
    """The panel's button must keep working for a plain logged-in account."""
    from app.config import settings

    monkeypatch.setattr(settings, "admin_emails", "someone-else@example.com")
    r = await non_admin_client.post("/api/vocab/enrich/requeue",
                                    json={"scope": "low_confidence"})
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "requeued": 7}
