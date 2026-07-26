"""Resolving an inflected form to the headword that carries its card.

The bug this guards against was measured on the live search on 2026-07-26 and it
was not subtle: `ist` (zipf 7.08, the commonest verb form in German) answered
`Ist-Wert` "фактическое значение", `mich` answered `Michelin-Männchen`, `bin`
answered `Bingo`, `gibt` answered nothing at all. None of those forms has a card
— the enrichment prompt refuses word forms, correctly — so nothing matched
exactly and pg_trgm returned the nearest string it could find.

Most of what is asserted here is what must NOT happen: a verb paradigm must not
claim a pronoun, a separable verb must not be indexed under its finite half, and
a form that already has a card of its own must not be shadowed by a redirect.
"""
from __future__ import annotations

import pytest
from app.db.models import VocabCard, VocabCardTranslation, VocabForm
from app.vocab import inflect, mirror, norm
from app.vocab import search as search_mod


# ── pure expansion ───────────────────────────────────────────────────────────
def test_verb_paradigm_expands_to_its_cells():
    sein = {"praesens": {"ich": "bin", "du": "bist", "er": "ist", "wir": "sind",
                         "ihr": "seid", "sie": "sind"},
            "praeteritum": "war", "partizip2": "gewesen", "konjunktiv2": "wäre",
            "imperativ_du": "sei"}
    forms = {f for f, _de, _ru in inflect.paradigm_forms(sein, "verb")}
    assert {"bin", "bist", "ist", "sind", "war", "gewesen", "wäre", "sei"} <= forms


def test_separable_verb_is_not_indexed_under_its_finite_half():
    """`aufstehen` stores "stehe auf". Taking either token is wrong.

    The last token is the prefix, so `auf` would become a "form" of every
    separable verb in the dump. The first token is a form of `stehen`, not of
    `aufstehen` — and `stehen` has its own paradigm and its own card, so nothing
    is lost by dropping the cell entirely.
    """
    auf = {"praesens": {"ich": "stehe auf", "er": "steht auf"},
           "praeteritum": "stand auf", "partizip2": "aufgestanden"}
    forms = {f for f, _de, _ru in inflect.paradigm_forms(auf, "verb")}
    assert forms == {"aufgestanden"}
    assert "auf" not in forms and "stehe" not in forms and "steht" not in forms


def test_superlative_drops_its_particle():
    """"am besten" is one word plus a particle — here the WORD is last."""
    forms = {f for f, _de, _ru in
             inflect.paradigm_forms({"komparativ": "besser", "superlativ": "am besten"},
                                    "adj")}
    assert forms == {"besser", "besten"}


def test_noun_paradigm_yields_every_case_cell():
    haus = {"sg": {"nom": "Haus", "gen": "Hauses", "dat": "Haus", "akk": "Haus"},
            "pl": {"nom": "Häuser", "gen": "Häuser", "dat": "Häusern", "akk": "Häuser"}}
    forms = {f for f, _de, _ru in inflect.paradigm_forms(haus, "noun")}
    assert {"Hauses", "Häuser", "Häusern"} <= forms


def test_a_reflexive_verb_cannot_claim_the_pronoun():
    """The dump conjugates reflexives with the pronoun attached.

    `mich` arrives as a "form" of besinnen, erholen, verlieben and 24 more. It
    is the accusative of `ich` and nothing else — measured on the live paradigms,
    27 verbs claimed it.
    """
    assert inflect.is_blocked("mich")
    assert inflect.is_blocked("sich")
    assert inflect.is_blocked("uns")
    index = inflect.index_rows(iter([("besinnen", "verb", {"praesens": {"ich": "mich"}})]))
    assert "mich" not in index


def test_closed_class_covers_the_forms_no_dump_conjugates():
    """`morphology` holds noun/verb/adj only — zero pronouns, zero determiners."""
    cc = inflect.CLOSED_CLASS
    assert cc["mir"].base == "ich" and cc["mir"].ru == "мне"
    assert cc["ihn"].base == "er"
    assert cc["eine"].base == "ein"
    assert cc["diese"].base == "dieser"
    assert cc["meine"].base == "mein"
    # euer contracts before an ending: euer + en -> euren, never "eueren"
    assert "euren" in cc and "eueren" not in cc
    assert cc["unseren"].base == "unser"


def test_archaic_pronoun_genitive_yields_to_the_possessive():
    """`ihrer` is read as a possessive in modern German, not as a pronoun.

    Both parses exist. The pronoun genitive survives only in fixed literary
    turns ("gedenke meiner"), while "mit ihrer Mutter" is everyday — and `ihrer`
    sits at zipf 5.76. Answering with the archaism would hide the reading the
    learner actually met.
    """
    assert inflect.CLOSED_CLASS["ihrer"].base == "ihr"
    assert inflect.CLOSED_CLASS["seiner"].base == "sein"


# ── the index and the lookup, on real Postgres ───────────────────────────────
async def _card(session, lemma, ru, *, pos="other", article=None, zipf=5.0,
                morphology=None):
    session.add(VocabCard(
        lemma=lemma, lemma_norm=norm.fold_de(lemma), lemma_ascii=norm.ascii_de(lemma),
        level="unlisted", band="C1", pos=pos, article=article, ru=ru,
        confidence="high", data={"ru_all": [ru]}, zipf=zipf, morphology=morphology,
        source_created_at=0.0,
    ))
    session.add(VocabCardTranslation(lemma=lemma, idx=0, ru=ru, ru_norm=norm.fold_ru(ru)))
    await session.commit()


async def test_rebuild_indexes_a_verb_form_and_search_resolves_it(pg_session):
    await _card(pg_session, "sein", "быть", pos="verb", zipf=6.32,
                morphology={"praesens": {"ich": "bin", "er": "ist"},
                            "praeteritum": "war"})
    await _card(pg_session, "Ist-Wert", "фактическое значение", pos="noun",
                article="der", zipf=2.0)
    assert (await mirror.rebuild_forms(pg_session))["forms"] >= 3

    result = await search_mod.search(pg_session, "ist")
    assert result["items"][0]["lemma"] == "sein", "the lie: Ist-Wert used to win"
    assert result["items"][0]["matched_form"]["base"] == "sein"
    assert result["form_of"][0]["form"] == "ist"


async def test_case_of_the_query_decides_between_a_noun_and_a_verb_form(pg_session):
    """`Stand` is a card AND `stand` is the Präteritum of `stehen`.

    Both readings are true, so the case the user typed decides — the same signal
    `_by_relevance` already uses to keep `die` from answering `Die` "чип".
    German capitalises its nouns, so a lowercase `stand` asks for the verb.
    Neither answer is ever dropped; only the order changes.
    """
    await _card(pg_session, "Stand", "стенд, состояние", pos="noun", article="der",
                zipf=5.0)
    await _card(pg_session, "stehen", "стоять", pos="verb", zipf=5.9,
                morphology={"praeteritum": "stand"})
    await mirror.rebuild_forms(pg_session)

    lower = await search_mod.search(pg_session, "stand")
    assert _lemmas(lower)[0] == "stehen" and "Stand" in _lemmas(lower)
    assert [f["base"] for f in lower["form_of"]] == ["stehen"]

    upper = await search_mod.search(pg_session, "Stand")
    assert _lemmas(upper)[0] == "Stand", "a card spelled as typed is never displaced"


async def test_closed_class_survives_a_homograph_card(pg_session):
    """`einen` is a card — the rare verb "to unite" — and search answered it.

    The accusative of `ein` is one of the commonest words in German. Dropping
    the form link because a card exists under the same spelling would leave the
    lie exactly where PLANS A1 found it.
    """
    await _card(pg_session, "einen", "объединять", pos="verb", zipf=6.48)
    await _card(pg_session, "ein", "один, неопределённый артикль", zipf=6.91)
    await mirror.rebuild_forms(pg_session)

    result = await search_mod.search(pg_session, "einen")
    assert result["items"][0]["lemma"] == "einen"          # exact card still wins
    # …but the reader is told what they almost certainly typed.
    assert [f["base"] for f in result["form_of"]] == ["ein"]
    assert result["form_of"][0]["cell_ru"].startswith("unbestimmter Artikel")


async def test_a_form_whose_base_has_no_card_is_not_indexed(pg_session):
    """A dangling pointer is worse than no pointer: it promises a card we lack."""
    await _card(pg_session, "Ist-Wert", "фактическое значение", pos="noun",
                article="der", zipf=2.0)
    assert (await mirror.rebuild_forms(pg_session))["forms"] == 0
    result = await search_mod.search(pg_session, "ist")
    assert result["form_of"] == []


async def test_rebuild_is_idempotent(pg_session):
    await _card(pg_session, "geben", "давать", pos="verb", zipf=5.6,
                morphology={"praesens": {"er": "gibt"}})
    first = await mirror.rebuild_forms(pg_session)
    second = await mirror.rebuild_forms(pg_session)
    assert first["forms"] == second["forms"]
    rows = (await pg_session.execute(
        VocabForm.__table__.select().where(VocabForm.form == "gibt"))).all()
    assert len(rows) == 1


@pytest.mark.parametrize("query", ["мне", "прогресс"])
async def test_russian_queries_do_not_consult_the_form_index(pg_session, query):
    """The index is German-side only; a Cyrillic query has no form to resolve."""
    await _card(pg_session, "ich", "я", zipf=7.08)
    await mirror.rebuild_forms(pg_session)
    result = await search_mod.search(pg_session, query)
    assert "form_of" not in result


async def test_a_capitalised_homograph_no_longer_outranks_the_form(pg_session):
    """`Mir` (персидский ковёр) answered a query for the dative of `ich`.

    Folding is case- and umlaut-blind, so the noun scores a perfect exact match
    against a lowercase query and wins on the old gate. German capitalises its
    nouns: someone who typed `mir` did not mean the carpet. Same shape as
    `Muss`/`muss`, `Einer`/`einer` and `Würde`/`wurde`.
    """
    await _card(pg_session, "Mir", "мир (ковёр)", pos="noun", article="der", zipf=6.32)
    await _card(pg_session, "ich", "я", zipf=7.08)
    await mirror.rebuild_forms(pg_session)

    result = await search_mod.search(pg_session, "mir")
    assert _lemmas(result)[0] == "ich"
    assert "Mir" in _lemmas(result), "the noun stays reachable, just not first"


async def test_the_capitalised_word_still_wins_when_it_is_what_was_typed(pg_session):
    await _card(pg_session, "Mir", "мир (ковёр)", pos="noun", article="der", zipf=6.32)
    await _card(pg_session, "ich", "я", zipf=7.08)
    await mirror.rebuild_forms(pg_session)
    assert _lemmas(await search_mod.search(pg_session, "Mir"))[0] == "Mir"


def _lemmas(result) -> list[str]:
    return [i["lemma"] for i in result["items"]]
