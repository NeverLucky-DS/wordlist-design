"""Wörterbuch lookup — a dictionary search, not a translator.

The user types a word and gets the closest entries from our own base: Latin
input searches the German lemma, Cyrillic searches the Russian meanings. No LLM
is involved — this resolves concrete words we already have, and if a word is
genuinely absent we say so rather than invent it.

Forgiveness comes from pg_trgm. Measured on the real base:
  зависимостью → зависимость  0.79   fortschrit → fortschritt  0.77
  прогрессы    → прогресс     0.73   grun       → grün         0.38
  кошка        → прогресс     0.00
which sits comfortably above the 0.3 default threshold for genuine matches and
at zero for noise, so inflected forms and typos land while junk does not.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import Float, case, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VocabCard, VocabCardTranslation
from app.vocab import norm
from app.vocab.topics import TOPICS

# Cards store a topic slug; the UI is German, so resolve it to the German label
# here rather than shipping the whole taxonomy to the browser.
_TOPIC_DE = {t["slug"]: t["de"] for t in TOPICS}

MAX_LIMIT = 50
# Below three characters a trigram match is mostly noise, so those queries run
# prefix-only. pg_trgm pads short strings and would still return something, but
# "ab" scoring against every "ab*" in 100k lemmas is not a useful ranking.
MIN_TRIGRAM_CHARS = 3

_EXACT = 2.0    # folded query == folded entry
_PREFIX = 1.0   # entry starts with the query; + similarity to order within
_PRIMARY_BONUS = 0.05  # tie-break toward a card's main meaning


def _by_relevance(score):
    """Order hits: match quality, headwords before forms, frequency, then length.

    Frequency has to sit above length. Every exact hit for "быстрый" scores the
    same 2.0, so the tie used to fall straight to `length(lemma_norm)` — which
    answered fix, rasch, prompt, rapide, zügig and put `schnell`, the 354th most
    common word in German, LAST. Someone looking up "быстрый" wants schnell.
    NULLS LAST keeps the few cards with no source frequency out of the top.

    But frequency cannot be trusted on its own, which is why `form_kind` sits
    above it. `wordfreq` folds case and counts surface forms, so the dictionary's
    non-headwords carry borrowed weight: `Schnell` (a combining form) wears the
    5.51 of the adjective, `gemacht` the weight of every "hat gemacht" written.
    Sorted by zipf alone those win, and "обманывать" answered `linken` — a rare
    slang verb holding the frequency of `link` — above täuschen and betrügen.
    Ordering by `form_kind IS NULL` first puts real words ahead of forms at equal
    match quality, while leaving a form reachable when nothing else matches.
    """
    return (
        score.desc(),
        VocabCard.form_kind.is_(None).desc(),
        VocabCard.zipf.desc().nullslast(),
        func.length(VocabCard.lemma_norm),
        VocabCard.lemma,
    )


def _like_prefix(folded: str) -> str:
    """LIKE pattern for `folded*`, with the wildcards in user input defused."""
    escaped = folded.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped + "%"


def _score(column, folded: str, prefix: str):
    sim = func.similarity(column, folded)
    return case(
        (column == folded, literal(_EXACT, Float)),
        (column.like(prefix, escape="\\"), literal(_PREFIX, Float) + sim),
        else_=sim,
    )


def _match(column, folded: str, prefix: str):
    """Index-usable predicate. `%` and LIKE both ride the GIN trigram index."""
    like = column.like(prefix, escape="\\")
    if len(folded) < MIN_TRIGRAM_CHARS:
        return like
    return or_(column.op("%")(folded), like)


def _collapse_synonyms(rows: list[tuple[VocabCard, float, str]],
                       limit: int) -> list[dict[str, Any]]:
    """Group cards that answer the query with the SAME Russian meaning.

    Reverse lookup asks a question the base was not written to answer. Each card
    was enriched alone, knowing nothing of its neighbours, so five of them claim
    the bare meaning "перевод" — Übersetzung, Übertragung, Verlegung, Translation
    and Umschaltung — and a flat list presents all five as equal answers to
    "перевод". They are not equal: they are synonyms of one sense, and only one
    of them is what a learner means.

    So the matched meaning is the group key, the most frequent card in the group
    heads it, and the rest ride along as `syn` — the shape Yandex.Dictionary uses
    (`tr` with nested `syn`) and Linguee renders as "less common". Nothing is
    dropped; the answer just stops being a wall. Rows arrive already ordered by
    relevance, so the first card of each group is its head and the groups keep
    the order their heads had.
    """
    groups: dict[str, list[tuple[VocabCard, float]]] = {}
    for card, score, meaning in rows:
        groups.setdefault(meaning, []).append((card, score))
    out: list[dict[str, Any]] = []
    for meaning, members in list(groups.items())[:limit]:
        head_card, head_score = members[0]
        item = card_out(head_card, head_score)
        item["meaning"] = meaning
        item["syn"] = [card_out(c, s) for c, s in members[1:]]
        out.append(item)
    return out


def card_out(card: VocabCard, score: float | None = None) -> dict[str, Any]:
    """Shape a card for the UI: promoted columns + the enriched JSON, plus the
    two derived fields the frontend paints with (`band`, `type`)."""
    data = dict(card.data or {})
    out = {
        "lemma": card.lemma,
        "ru": card.ru,
        "ru_all": data.get("ru_all") or ([card.ru] if card.ru else []),
        "level": card.level,
        "band": card.band,
        "type": norm.type_of(card.pos, card.article),
        "pos": card.pos,
        "article": card.article,
        "topic": card.topic,
        "topic_de": _TOPIC_DE.get(card.topic or "", ""),
        "confidence": card.confidence,
        "register": card.register,
        # Non-NULL means the source listed this as a form, not a headword; the UI
        # labels it ("форма от machen") instead of passing it off as a word.
        "form_kind": card.form_kind,
        "form_of": card.form_of,
        "definition_de": data.get("definition_de") or "",
        "grammar": data.get("grammar") or {},
        "rektion": data.get("rektion") or "",
        "synonyms": data.get("synonyms") or [],
        "collocations": data.get("collocations") or [],
        "examples": data.get("examples") or [],
    }
    if score is not None:
        out["score"] = round(float(score), 4)
    return out


def _de_terms(q: str) -> list[tuple[Any, str, str]]:
    """Query both German spellings of the index, scoring against the better hit.

    `lemma_norm` holds the correct substitution (grün→gruen), `lemma_ascii` the
    flattened one (grün→grun). BOTH columns are always searched: what differs
    between them is the *stored* word, not the query. Someone typing "grun" folds
    to "grun" either way, yet only `lemma_ascii` carries "grun" for grün — skip
    that column and grün never surfaces (measured: Grund and Grunzen outrank it).
    """
    folded, flat = norm.fold_de(q), norm.ascii_de(q)
    return [
        (VocabCard.lemma_norm, folded, _like_prefix(folded)),
        (VocabCard.lemma_ascii, flat, _like_prefix(flat)),
    ]


async def search(db: AsyncSession, q: str, limit: int = 20) -> dict[str, Any]:
    """Look `q` up on whichever side its script implies."""
    limit = max(1, min(int(limit), MAX_LIMIT))
    lang = norm.detect_lang(q)
    folded = norm.fold_ru(q) if lang == "ru" else norm.fold_de(q)
    if not folded:
        return {"lang": lang, "query": q, "items": []}
    prefix = _like_prefix(folded)

    if lang == "ru":
        # A word matches if ANY of its meanings does, and is scored by its best
        # one — but WHICH meaning that was has to survive the query, because it
        # is what tells synonyms of one sense apart from separate answers.
        t = VocabCardTranslation
        scored = (
            select(
                t.lemma.label("lemma"),
                t.ru.label("meaning"),
                (_score(t.ru_norm, folded, prefix)
                 + case((t.idx == 0, literal(_PRIMARY_BONUS, Float)),
                        else_=literal(0.0, Float))).label("score"),
            )
            .where(_match(t.ru_norm, folded, prefix))
            .subquery()
        )
        best = (
            select(scored.c.lemma, scored.c.meaning, scored.c.score)
            .distinct(scored.c.lemma)
            .order_by(scored.c.lemma, scored.c.score.desc())
            .subquery()
        )
        stmt = (
            select(VocabCard, best.c.score, best.c.meaning)
            .join(best, VocabCard.lemma == best.c.lemma)
            .order_by(*_by_relevance(best.c.score))
            .limit(MAX_LIMIT)
        )
        rows = (await db.execute(stmt)).all()
        return {
            "lang": lang,
            "query": q,
            "items": _collapse_synonyms(list(rows), limit),
        }
    else:
        terms = _de_terms(q)
        scores = [_score(col, term, pfx) for col, term, pfx in terms]
        score = scores[0] if len(scores) == 1 else func.greatest(*scores)
        matches = [_match(col, term, pfx) for col, term, pfx in terms]
        stmt = (
            select(VocabCard, score.label("score"))
            .where(or_(*matches))
            .order_by(*_by_relevance(score))
            .limit(limit)
        )

    rows = (await db.execute(stmt)).all()
    return {
        "lang": lang,
        "query": q,
        "items": [card_out(card, score) for card, score in rows],
    }
