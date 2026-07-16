"""Server-side vocab enrichment — FORMAT + STORAGE (Phase 2).

Model (decided 2026-07-13): the SERVER runs enrichment. Each authenticated
account attaches its own Mistral key (encrypted in Postgres); a background
worker (see `enrich_worker.py`) claims work and calls Mistral through
`app.services.mistral_http` with that account's key. The browser only
starts/stops and watches progress.

Storage split (the "формат сохранения"):
  • GENERAL INFO  → `vocab.db` `words` — raw dictionary data. IMMUTABLE, rebuilt
    only by `build.py`. Opened read-only here (ATTACH). The INPUT we send as-is.
  • WORK STATE    → `enrichment.db` `word_status` — per-lemma status/lease/attempts.
    Lives in the DURABLE db, NOT vocab.db, so rebuilding vocab.db never loses
    progress. A `failed` terminal state + attempt cap kill the poison-word loop.
  • CARD          → `enrichment.db` `cards` — the validated extended card as JSON
    plus promoted columns (topic/ru/…) and provenance (model, prompt_version,
    enriched_by). The OUTPUT the app shows.

Bump PROMPT_VERSION when the prompt/schema changes so re-enrichment can target
stale cards without re-doing good ones.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from app.vocab import norm
from app.vocab.topics import GENERAL_TOPIC, TOPICS, TOPIC_SLUGS

# ── config ───────────────────────────────────────────────────────────────────
VOCAB_DB = Path(os.environ.get("VOCAB_DB") or Path(__file__).with_name("vocab.db"))
ENRICH_DB = Path(os.environ.get("ENRICH_DB") or VOCAB_DB.with_name("enrichment.db"))

# Bump when the prompt/schema changes so re-enrichment can target stale cards.
# 2026-07-14: added model-side skip (reject non-words) + stronger ru_all.
# 2026-07-17: skip inflected forms (hast/Stunden/gemacht got invented rare
#             readings); allow "word" to carry the post-1996 spelling.
PROMPT_VERSION = "enrich-2026-07-17"
CARD_SCHEMA = 1

DEFAULT_BATCH = 10          # bench sweet spot (throughput flat, latency bounded)
MAX_BATCH = 20
STALE_LEASE = 300.0         # s; a crashed worker's words free after this
MAX_ATTEMPTS = 3            # after this many failures a lemma is terminal 'failed'

# guard rails against a pathological raw row blowing the token budget
_MAX_FIELD_CHARS = 700
_MAX_LIST_ITEMS = 12

_POS = {"noun", "verb", "adj", "adv", "other"}
_ARTICLES = {"der", "die", "das"}
_REGISTERS = {"neutral", "gehoben", "umgangssprachlich", "fachsprachlich"}
_GRAMMAR_KEYS = {
    "noun": ("genitiv", "plural"),
    "verb": ("praeteritum", "partizip2", "hilfsverb"),
    "adj": ("komparativ", "superlativ"),
}
_SLUGSET = set(TOPIC_SLUGS)
_TOPIC_LINES = "\n".join(f"{t['slug']} = {t['de']}" for t in TOPICS)

# ── junk pre-filter (spend no tokens on non-headwords) ───────────────────────
# vocab.db keeps case-differing duplicates (er/Er/ER), word-formation fragments
# (mit-, a-, -heit, Tag-) and all-caps acronyms (EU, SPD) as separate lemmas.
# None of these are learnable B2–C1 dictionary headwords, and a bare "ER"/"DER"
# makes the model hallucinate a rare reading. We never serve them: they are
# excluded from `claim` in SQL and reported as `junk` in progress. The stored
# `skipped` status is reserved for words the MODEL itself rejects (see skip_words).
#
# SQLite upper()/GLOB are ASCII-only, which is exactly the junk we target here.
JUNK_SQL = (
    "(w.lemma GLOB '*-' OR w.lemma GLOB '-*' "     # trailing/leading hyphen fragment
    "OR length(w.lemma) < 2 "                       # single char
    "OR (w.lemma = upper(w.lemma) AND w.lemma GLOB '*[A-Za-z]*'))"  # all-caps acronym
)

_HYPHEN = re.compile(r"(^-)|(-$)")


def is_junk(lemma: str) -> bool:
    """Python twin of JUNK_SQL — a lemma not worth an LLM call."""
    s = (lemma or "").strip()
    if len(s) < 2:
        return True
    if s[0] == "-" or s[-1] == "-":
        return True
    if s == s.upper() and any(c.isalpha() for c in s):
        return True
    return False


# ── phases ───────────────────────────────────────────────────────────────────
# One button, several kinds of work. A phase is NOT a coordinator: it is a tag on
# word_status, and `claim` simply serves the highest-priority phase that still has
# work. So N accounts need no leader election — they converge on the same phase
# because they read the same table, and a crash loses nothing.
#
# Repairs run before the backfill on purpose: they are ~1.7k words against ~17k,
# and they exercise the response matcher on a small, known-answer set first. If
# something is wrong with it, it shows up in minutes instead of at 4am.
BACKFILL = "backfill"
PHASES: tuple[tuple[str, str], ...] = (
    ("repair_case", "Починка омографов"),
    ("repair_ortho", "Починка орфографии"),
    (BACKFILL, "Обогащение новых слов"),
)
PHASE_PRIO = {name: i for i, (name, _) in enumerate(PHASES)}

# enrich order: obligatory Goethe core first, then upper levels, then the tail
_LEVEL_PRIO = {"a1": 0, "a2": 1, "b1": 2, "b2": 3, "c1": 4, "c2": 5, "unlisted": 6}
_JSON_FIELDS = ("pos", "forms", "translations", "examples", "synonyms",
                "collocations", "idioms", "sources", "by_source")
_RAW_FIELDS = ("lemma", "level", "article", "zipf", "freq_rank", "pos", "forms",
               "translations", "examples", "synonyms", "collocations",
               "idioms", "sources", "by_source")

PROMPT = """Du bist ein zweisprachiges (Deutsch–Russisch) Lexikon-Redaktionssystem für DaF (B2–C1).
Das Ergebnis wird DIREKT zu Lernkarten (Vokabeltrainer) und zu einer vollständigen
Wort-Detailseite mit Grammatik und Beispielen. Qualität geht IMMER vor Vollständigkeit.
Unten stehen {count} deutsche Wörter mit Rohdaten aus unserer Wörterbuch-Datenbank
(lemma, level, zipf, alle Felder und by_source pro Quelle). Bearbeite ALLE Wörter.
Die Rohdaten sind oft verrauscht (OCR-Reste, veraltete/falsche Angaben, falscher
Artikel) — KORRIGIERE das nach deinem Sprachwissen; übernimm keinen Müll.

Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Markdown):
{{"words": [
  {{
    "word": "<exakt lemma aus den Rohdaten>",
    "skip": false,
    "skip_reason": "",
    "pos": "noun | verb | adj | adv | other",
    "article": "der | die | das  (nur Substantive, sonst null)",
    "ru": "самый частотный современный перевод (1-3 слова)",
    "ru_all": ["ВСЕ употребимые значения, важнейшее первым (обычно 2-4)"],
    "definition_de": "Kurze deutsche Definition in EINEM Satz (B2).",
    "grammar": {{
      "genitiv": "des …", "plural": "die …",
      "praeteritum": "…", "partizip2": "…", "hilfsverb": "haben | sein",
      "komparativ": "…", "superlativ": "am …"
    }},
    "rektion": "z.B. 'für + Akk.' oder \"\"",
    "synonyms": ["1-3 saubere deutsche Synonyme"],
    "collocations": ["1-3 typische Kollokationen"],
    "topic": "<GENAU EIN slug aus der TOPIC-LISTE>",
    "register": "neutral | gehoben | umgangssprachlich | fachsprachlich",
    "confidence": "high | low",
    "examples": [{{"de": "Satz mit **Wort** fett.", "ru": "перевод."}}]
  }}
]}}

AUSSORTIEREN (das Wichtigste zuerst):
- Setze "skip": true (und kurzen "skip_reason") und LASS alle anderen Felder weg,
  wenn das lemma KEIN eigenständiges, lernbares Wörterbuch-Wort ist:
  · OCR-/Datenmüll, Buchstabensalat, kein echtes deutsches Wort;
  · Eigenname (Personen, Orte, Marken, Institutionen — Oder, Man, DER als Firma);
  · Abkürzung / Akronym (EU, SPD, usw.);
  · Wortbildungs-Fragment oder Affix (mit-, ab-, -heit, Tag-);
  · FLEKTIERTE WORTFORM statt Grundform: "hast"/"hat" (→ haben), "stand" (→ stehen),
    "galt" (→ gelten), "Stunden" (→ Stunde), "gemacht"/"gegeben" (→ machen/geben),
    "einen" (Akk. von "ein"), "jungen" (→ jung). Das Lemma ist die Grundform;
    eine Form davon ist KEIN eigener Eintrag → skip. Rette sie NIEMALS mit einer
    seltenen Nebenbedeutung, die es zufällig auch gibt: kein "einen"=vereinen,
    kein "stunden"=aufschieben für "Stunden", kein "Hast"=Eile für "hast".
    ABER: ist die Schreibung selbst ein übliches eigenes Lemma, behalte sie —
    "Macht", "Würde", "Art", "Recht", "Halt" (Substantive) und substantivierte
    Adjektive ("das Ganze", "der Alte") sind echte Einträge.
  · Groß-/Kleinschreibungs-Artefakt: Substantive schreibt man IMMER groß, also ist
    eine kleingeschriebene Nomen-Form ("nacht", "zeit", "platz") ein Artefakt → skip,
    behalte nur "Nacht"/"Zeit". Umgekehrt ist ein großgeschriebenes Funktions-/Nicht-
    Substantiv am Satzanfang ("Aber", "Ja", "Unter", "Für", "Er") ein Artefakt → skip;
    erfinde dafür KEINE Substantiv-Bedeutung (kein "Unter"=Spielkarte, kein "Ja"=Zustimmung).
  · fremdsprachiges Wort ohne echten deutschen Gebrauch.
  Erfinde NIEMALS eine seltene/konstruierte Bedeutung, nur um ein Wort zu "retten".
- Kommen im selben Batch dieselbe Schreibung groß UND klein vor, behalte nur die
  richtige Wortart (Substantiv groß, Verb/Adjektiv/Adverb/Funktionswort klein) und
  setze die andere auf "skip". Bei echt getrennten Wörtern (z.B. "Morgen"=утро /
  "morgen"=завтра, "Essen"=еда / "essen"=есть) BEIDE behalten, aber mit KORREKT
  unterschiedlicher Wortart und Bedeutung — niemals identisch kopieren.
- "confidence": "low" NUR für ein ECHTES Wort, dessen Bedeutung/Grammatik du nicht
  sicher weißt. Ist es kein echtes Wort → "skip", nicht "low".

REGELN für behaltene Wörter (skip=false):
- "word" MUSS exakt dem lemma entsprechen (Zuordnung) — Groß-/Kleinschreibung
  inklusive. EINZIGE Ausnahme: das lemma steht in der VERALTETEN Rechtschreibung
  von vor 1996 (Schluß, Prozeß, Einfluß, bißchen, muß, Bewußtsein). Dann gib in
  "word" die HEUTIGE amtliche Schreibung zurück (Schluss, Prozess, Einfluss,
  bisschen, muss, Bewusstsein) — wir speichern die Karte unter dieser.
  ß nach langem Vokal oder Diphthong ist KORREKT und bleibt (Straße, groß, weiß,
  heißen, Maß, Fuß) — ändere diese Wörter NICHT.
- "ru_all": ALLE gängigen Bedeutungen als getrennte Einträge, wichtigste zuerst;
  bei echter Polysemie mindestens 2. "ru" = das erste/häufigste davon.
- "grammar": NUR die zur Wortart passenden Schlüssel; Rest weglassen.
- "topic": MUSS exakt ein slug aus der Liste sein (nicht erfinden).
- "examples": GENAU 3 natürliche B2-Sätze, das Wort **fett**.
- "synonyms"/"collocations": echte, sonst [].

TOPIC-LISTE (slug = deutsche Bezeichnung):
{topics}

Eingabewörter (Roh-JSON pro Wort):
{words_block}
"""


# ── prompt building ──────────────────────────────────────────────────────────
def _clip(val: Any) -> Any:
    if isinstance(val, str):
        return val[:_MAX_FIELD_CHARS]
    if isinstance(val, list):
        return [v[:_MAX_FIELD_CHARS] if isinstance(v, str) else v
                for v in val[:_MAX_LIST_ITEMS]]
    if isinstance(val, dict):
        return {k: _clip(v) for k, v in val.items()}
    return val


def raw_view(row: dict) -> dict:
    return {f: _clip(row.get(f)) for f in _RAW_FIELDS}


def build_prompt(rows: list[dict]) -> str:
    block = "\n\n".join(
        f"--- Wort {i}: {r['lemma']} ---\n{json.dumps(raw_view(r), ensure_ascii=False)}"
        for i, r in enumerate(rows, 1))
    return PROMPT.format(count=len(rows), topics=_TOPIC_LINES, words_block=block)


# ── response validation / normalization ──────────────────────────────────────
def _clean_list(val: Any, limit: int) -> list[str]:
    if not isinstance(val, list):
        return []
    out: list[str] = []
    for v in val:
        if isinstance(v, str) and v.strip() and v.strip() not in out:
            out.append(v.strip())
        if len(out) >= limit:
            break
    return out


def _norm_grammar(pos: str, grammar: Any) -> dict:
    if not isinstance(grammar, dict):
        return {}
    return {k: grammar[k].strip() for k in _GRAMMAR_KEYS.get(pos, ())
            if isinstance(grammar.get(k), str) and grammar[k].strip()}


def normalize_card(item: dict) -> dict | None:
    """Validate + normalize one model item into a persist-ready card, or None
    if it's unusable (missing mandatory core) so the word can be retried."""
    if not isinstance(item, dict):
        return None
    ru = item.get("ru")
    definition = item.get("definition_de")
    if not (isinstance(ru, str) and ru.strip()):
        return None
    if not (isinstance(definition, str) and definition.strip()):
        return None

    examples = []
    if isinstance(item.get("examples"), list):
        for ex in item["examples"]:
            if (isinstance(ex, dict) and isinstance(ex.get("de"), str)
                    and isinstance(ex.get("ru"), str)
                    and ex["de"].strip() and ex["ru"].strip()):
                examples.append({"de": ex["de"].strip(), "ru": ex["ru"].strip()})
            if len(examples) >= 3:
                break
    if not examples:
        return None

    pos = item.get("pos")
    pos = pos if pos in _POS else "other"
    article = item.get("article")
    article = article if (pos == "noun" and article in _ARTICLES) else None
    topic = item.get("topic")
    topic = topic if topic in _SLUGSET else GENERAL_TOPIC
    register = item.get("register")
    register = register if register in _REGISTERS else "neutral"
    confidence = "low" if item.get("confidence") == "low" else "high"
    rektion = item.get("rektion")
    rektion = rektion.strip() if isinstance(rektion, str) else ""

    return {
        "schema": CARD_SCHEMA,
        "pos": pos,
        "article": article,
        "ru": ru.strip(),
        "ru_all": _clean_list(item.get("ru_all"), 4) or [ru.strip()],
        "definition_de": definition.strip(),
        "grammar": _norm_grammar(pos, item.get("grammar")),
        "rektion": rektion,
        "synonyms": _clean_list(item.get("synonyms"), 4),
        "collocations": _clean_list(item.get("collocations"), 4),
        "topic": topic,
        "register": register,
        "confidence": confidence,
        "examples": examples,
    }


def _is_skip(item: Any) -> bool:
    return isinstance(item, dict) and item.get("skip") is True


def parse_response(
    sent_lemmas: list[str], parsed: dict
) -> tuple[dict[str, dict], list[str], list[str], dict[str, str]]:
    """Map a Mistral response back to sent words.

    Returns (cards_by_lemma, skipped, unmatched, renamed):
      • cards    — validated cards to persist and mark 'done', keyed by the SENT
                   lemma (the work-state key);
      • skipped  — words the MODEL rejected as non-headwords (terminal 'skipped',
                   no card, never retried);
      • unmatched — words dropped or returned invalid; a failed attempt so the
                    word is retried until MAX_ATTEMPTS;
      • renamed  — sent lemma → the lemma the card should be STORED under, for
                   the pre-1996 spellings the model modernizes (Schluß→Schluss).
    Never lose a word to a partial batch — every sent lemma lands in exactly one
    bucket.

    Matching is exact-first and deliberately refuses to guess. It used to fold
    case (`by_word[word.lower()]`), which silently merged the two halves of every
    homograph pair sent together: the model answered Morgen=утро AND morgen=завтра
    correctly, the index kept one, and BOTH lemmas were saved with it. 635 pairs
    in the base were byte-identical duplicates because of it — `morgen`=завтра did
    not exist at all. Case is the ONLY thing separating those two words, so it can
    never be folded away during lookup.

    The folded fallback exists for a different failure: the model is told to
    correct pre-1996 spellings, so "Schluß" comes back as "Schluss" and never
    matched by name (348 words dead in `failed`, incl. Bewusstsein, Einfluss,
    Prozess). It only fires when the fold is UNAMBIGUOUS on both sides — one sent
    lemma and one returned item — so a Morgen/morgen batch can never reach it.
    """
    items = parsed.get("words") if isinstance(parsed, dict) else None
    exact: dict[str, dict] = {}
    by_fold: dict[str, list[dict]] = {}
    if isinstance(items, list):
        for it in items:
            if not (isinstance(it, dict) and isinstance(it.get("word"), str)):
                continue
            word = it["word"].strip()
            if not word:
                continue
            exact.setdefault(word, it)
            by_fold.setdefault(norm.fold_de(word), []).append(it)

    # How many SENT lemmas share a folded key. >1 means the fold cannot identify
    # a word (Morgen/morgen) and only an exact hit may be trusted.
    sent_folds: dict[str, int] = {}
    for lemma in sent_lemmas:
        key = norm.fold_de(lemma)
        sent_folds[key] = sent_folds.get(key, 0) + 1

    cards: dict[str, dict] = {}
    skipped: list[str] = []
    unmatched: list[str] = []
    renamed: dict[str, str] = {}
    for lemma in sent_lemmas:
        item = exact.get(lemma)
        store_as = lemma
        if item is None:
            key = norm.fold_de(lemma)
            candidates = by_fold.get(key, [])
            if sent_folds[key] == 1 and len(candidates) == 1:
                item = candidates[0]
                word = item["word"].strip()
                # A pure case difference means the model just re-cased our lemma;
                # keep OUR spelling, it is the homograph key. A deeper difference
                # is the orthography correction we asked for — store under theirs.
                if word.lower() != lemma.lower():
                    store_as = word
        if _is_skip(item):
            skipped.append(lemma)
            continue
        card = normalize_card(item) if item else None
        if card:
            cards[lemma] = card
            if store_as != lemma:
                renamed[lemma] = store_as
        else:
            unmatched.append(lemma)
    return cards, skipped, unmatched, renamed


# ── storage (enrichment.db; vocab.db attached read-only) ─────────────────────
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(ENRICH_DB), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    if VOCAB_DB.exists():
        con.execute("ATTACH DATABASE ? AS v", (str(VOCAB_DB),))
    return con


def _add_column(con: sqlite3.Connection, table: str, column: str, decl: str) -> None:
    """Idempotent ALTER — the live enrichment.db is 100 MB and predates these
    columns, so the schema has to grow in place rather than be recreated."""
    have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
    if column not in have:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def ensure_schema() -> None:
    con = sqlite3.connect(str(ENRICH_DB), timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("""CREATE TABLE IF NOT EXISTS word_status(
            lemma TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'raw',   -- raw | done | failed | skipped
            attempts INTEGER NOT NULL DEFAULT 0,
            lease_owner INTEGER,                  -- user_id
            lease_at REAL,
            updated_at REAL)""")
        con.execute("CREATE INDEX IF NOT EXISTS ix_ws_status ON word_status(status)")
        con.execute("""CREATE TABLE IF NOT EXISTS cards(
            lemma TEXT PRIMARY KEY,
            level TEXT, topic TEXT, pos TEXT, article TEXT, ru TEXT,
            confidence TEXT, register TEXT,
            data TEXT,                            -- full extended card JSON
            model TEXT, prompt_version TEXT, schema_version INTEGER,
            enriched_by INTEGER,                  -- user_id
            created_at REAL)""")
        con.execute("CREATE INDEX IF NOT EXISTS ix_cards_topic ON cards(topic)")
        # Which kind of work a word is queued for; NULL reads as the backfill.
        _add_column(con, "word_status", "phase", "TEXT")
        con.execute("CREATE INDEX IF NOT EXISTS ix_ws_phase ON word_status(phase)")
        # Frequency, carried over from vocab.db so search can rank by it without
        # joining across databases (the mirror only ever reads `cards`).
        _add_column(con, "cards", "zipf", "REAL")
        # What each account's key has spent. Lives here, next to the rest of the
        # work state, because the worker is a sync thread that already owns this
        # file — routing it to Postgres would mean an event loop per worker.
        # Bucketed by UTC day so the fleet panel can show today apart from ever.
        con.execute("""CREATE TABLE IF NOT EXISTS token_usage(
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,                    -- UTC, YYYY-MM-DD
            calls INTEGER NOT NULL DEFAULT 0,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            updated_at REAL,
            PRIMARY KEY(user_id, day))""")
        con.commit()
    finally:
        con.close()


def _raw_word(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in _JSON_FIELDS:
        if isinstance(d.get(f), str):
            try:
                d[f] = json.loads(d[f])
            except json.JSONDecodeError:
                d[f] = []
    return {k: d.get(k) for k in _RAW_FIELDS}


# A word is up for grabs: no terminal status, attempts left, no live lease.
_CLAIMABLE = ("COALESCE(ws.status,'raw')='raw' "
              "AND COALESCE(ws.attempts,0) < ? "
              "AND (ws.lease_at IS NULL OR ws.lease_at < ?)")


def _order_clause() -> str:
    levels = " ".join(f"WHEN '{lvl}' THEN {p}" for lvl, p in _LEVEL_PRIO.items())
    phases = " ".join(f"WHEN '{n}' THEN {p}" for n, p in PHASE_PRIO.items())
    return (f"ORDER BY CASE COALESCE(ws.phase,'{BACKFILL}') {phases} ELSE 9 END, "
            f"CASE w.level {levels} ELSE 9 END, w.freq_rank")


def case_partners(lemma: str) -> set[str]:
    """The spellings of `lemma` that differ from it only in case.

    Python's `.lower()`/`.upper()` and not SQL's: SQLite folds ASCII only, so
    `lower('Über')` is still 'Über' and an Über/über pair would slip through.
    """
    out = {lemma.lower(), lemma[:1].upper() + lemma[1:]} if lemma else set()
    out.discard(lemma)
    return out


def _with_case_partners(con: sqlite3.Connection, rows: list, stale_before: float,
                        cap: int) -> list:
    """Pull a claimed word's case twin into the SAME batch.

    The prompt can only resolve a homograph pair (keep "Morgen"=утро, "morgen"=
    завтра; skip the artifact in "nacht"/"Nacht") when it sees both spellings at
    once. Ordering by freq_rank puts them next to each other but a batch boundary
    can still split them — then each is judged alone and the artifact survives as
    a second card. So co-claiming is explicit rather than left to luck.

    `cap` holds the grown batch to MAX_BATCH — partners must not silently turn a
    tested prompt size into double one. At DEFAULT_BATCH (10) that still leaves
    room for a partner to every word, which is what the repair phase actually
    hits: measured on the live base, its batches come out 100% pairs.
    """
    if cap <= 0:
        return list(rows)
    have = {r["lemma"] for r in rows}
    wanted = set()
    for r in rows:
        wanted |= case_partners(r["lemma"])
    wanted -= have
    if not wanted:
        return list(rows)
    wanted = sorted(wanted)[:cap]
    qs = ",".join("?" * len(wanted))
    extra = con.execute(
        f"""SELECT w.* FROM v.words w
            LEFT JOIN word_status ws ON ws.lemma = w.lemma
            WHERE w.lemma IN ({qs}) AND {_CLAIMABLE} AND NOT {JUNK_SQL}""",
        [*wanted, MAX_ATTEMPTS, stale_before],
    ).fetchall()
    return list(rows) + list(extra)


def claim(user_id: int, n: int = DEFAULT_BATCH) -> list[dict]:
    """Atomically lease up to n words that are raw, not failed, not fresh-leased.

    All state changes happen in enrichment.db under BEGIN IMMEDIATE, so many
    workers never grab the same word. Returns decoded raw rows (the LLM input).
    """
    ensure_schema()
    if not VOCAB_DB.exists():
        return []
    n = max(1, min(int(n), MAX_BATCH))
    now = time.time()
    stale_before = now - STALE_LEASE
    con = _conn()
    try:
        con.isolation_level = None
        con.execute("BEGIN IMMEDIATE")
        rows = con.execute(
            f"""SELECT w.* FROM v.words w
                LEFT JOIN word_status ws ON ws.lemma = w.lemma
                WHERE {_CLAIMABLE} AND NOT {JUNK_SQL}
                {_order_clause()}
                LIMIT ?""",
            (MAX_ATTEMPTS, stale_before, n),
        ).fetchall()
        rows = _with_case_partners(con, rows, stale_before,
                                   cap=MAX_BATCH - len(rows))
        for r in rows:
            con.execute(
                """INSERT INTO word_status(lemma,status,attempts,lease_owner,lease_at,updated_at)
                   VALUES(?, 'raw', 0, ?, ?, ?)
                   ON CONFLICT(lemma) DO UPDATE SET
                     lease_owner=excluded.lease_owner, lease_at=excluded.lease_at,
                     updated_at=excluded.updated_at""",
                (r["lemma"], user_id, now, now))
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    return [_raw_word(r) for r in rows]


def save_cards(user_id: int, cards: dict[str, dict], levels: dict[str, str],
               model: str, renamed: dict[str, str] | None = None,
               zipfs: dict[str, float] | None = None) -> int:
    """Persist validated cards and flip their status to 'done'. Idempotent.

    `cards` is keyed by the SENT lemma and so is `word_status` — that key is the
    work state and must stay pinned to vocab.db, or a word whose card is filed
    elsewhere would look unenriched and be served again forever.

    `renamed` files the CARD under a different lemma: the model returns the
    post-1996 spelling for a pre-reform entry (Schluß→Schluss), and the card is
    what the user reads, so it carries the modern word. The base has no separate
    'Schluss' row to collide with — checked: of 3371 ß-lemmas only 16 have an
    ss-twin — so this adds the modern spelling rather than shadowing one.
    """
    if not cards:
        return 0
    renamed = renamed or {}
    zipfs = zipfs or {}
    now = time.time()
    con = _conn()
    try:
        for lemma, c in cards.items():
            con.execute(
                """INSERT OR REPLACE INTO cards(lemma,level,topic,pos,article,ru,
                     confidence,register,data,model,prompt_version,schema_version,
                     enriched_by,created_at,zipf)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (renamed.get(lemma, lemma), levels.get(lemma), c["topic"],
                 c["pos"], c["article"], c["ru"], c["confidence"], c["register"],
                 json.dumps(c, ensure_ascii=False), model, PROMPT_VERSION,
                 CARD_SCHEMA, user_id, now, zipfs.get(lemma)))
            if lemma in renamed:
                # The old spelling keeps no card of its own; drop any stale one so
                # search cannot serve both "Schluß" and "Schluss".
                con.execute("DELETE FROM cards WHERE lemma=?", (lemma,))
            con.execute(
                """INSERT INTO word_status(lemma,status,attempts,lease_owner,lease_at,updated_at)
                   VALUES(?, 'done', 0, NULL, NULL, ?)
                   ON CONFLICT(lemma) DO UPDATE SET status='done', lease_owner=NULL,
                     lease_at=NULL, updated_at=excluded.updated_at""",
                (lemma, now))
        con.commit()
        return len(cards)
    finally:
        con.close()


def fail_words(lemmas: list[str]) -> None:
    """Count a failed attempt; flip to terminal 'failed' past MAX_ATTEMPTS so
    poison words stop being re-served forever."""
    if not lemmas:
        return
    now = time.time()
    con = _conn()
    try:
        for lemma in lemmas:
            con.execute(
                """INSERT INTO word_status(lemma,status,attempts,lease_owner,lease_at,updated_at)
                   VALUES(?, 'raw', 1, NULL, NULL, ?)
                   ON CONFLICT(lemma) DO UPDATE SET
                     attempts = word_status.attempts + 1,
                     status = CASE WHEN word_status.attempts + 1 >= ?
                                   THEN 'failed' ELSE 'raw' END,
                     lease_owner=NULL, lease_at=NULL, updated_at=excluded.updated_at""",
                (lemma, now, MAX_ATTEMPTS))
        con.commit()
    finally:
        con.close()


def skip_words(lemmas: list[str]) -> None:
    """Terminal 'skipped' — the model judged these not real learnable headwords.
    No card, never re-served, does NOT count as a failure.

    Drops any card the word already had: on a repair pass the model is re-judging
    a word we ALREADY published (the artifact half of a homograph pair, e.g. the
    noun card wrongly filed under "nacht"), and leaving it would keep the thing
    we just decided is not a word in the search index. Nothing is lost for good —
    vocab.db is immutable and a requeue re-enriches the lemma from scratch.
    """
    if not lemmas:
        return
    now = time.time()
    con = _conn()
    try:
        for lemma in lemmas:
            con.execute("DELETE FROM cards WHERE lemma=?", (lemma,))
            con.execute(
                """INSERT INTO word_status(lemma,status,attempts,lease_owner,lease_at,updated_at)
                   VALUES(?, 'skipped', 0, NULL, NULL, ?)
                   ON CONFLICT(lemma) DO UPDATE SET status='skipped',
                     lease_owner=NULL, lease_at=NULL, updated_at=excluded.updated_at""",
                (lemma, now))
        con.commit()
    finally:
        con.close()


def requeue(lemmas: list[str], *, drop_card: bool = True,
            phase: str | None = None) -> int:
    """Reset words back to 'raw' so a fresh run re-enriches them (with the current
    prompt). Clears attempts/lease and, by default, deletes the stale card so the
    old low-quality output can't linger. Returns how many were reset.

    `drop_card=False` keeps the old card visible until a better one replaces it —
    what the repair phases want, since they re-enrich words that are already live
    and a gap in search would be worse than a stale entry for a few minutes.
    """
    if not lemmas:
        return 0
    now = time.time()
    con = _conn()
    try:
        n = 0
        for lemma in lemmas:
            if drop_card:
                con.execute("DELETE FROM cards WHERE lemma=?", (lemma,))
            cur = con.execute(
                """INSERT INTO word_status(lemma,status,attempts,lease_owner,lease_at,updated_at,phase)
                   VALUES(?, 'raw', 0, NULL, NULL, ?, ?)
                   ON CONFLICT(lemma) DO UPDATE SET status='raw', attempts=0,
                     lease_owner=NULL, lease_at=NULL, updated_at=excluded.updated_at,
                     phase=excluded.phase""",
                (lemma, now, phase))
            n += cur.rowcount or 1
        con.commit()
        return n
    finally:
        con.close()


# ── token accounting ────────────────────────────────────────────────────────
def _utc_day() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def record_usage(user_id: int, usage: dict) -> None:
    """Add one Mistral reply's token cost to this account's tally.

    Reads only what Mistral sent: a reply with no `total_tokens` still counts as
    a call, because the call happened even if we cannot price it. Silently
    tolerates junk in the numbers — this is bookkeeping, and it must never be the
    reason a good batch is lost.
    """
    def _int(key: str) -> int:
        try:
            return max(0, int(usage.get(key) or 0))
        except (TypeError, ValueError):
            return 0

    ensure_schema()   # same contract as claim/progress: a public entry stands alone
    now = time.time()
    con = _conn()
    try:
        con.execute(
            """INSERT INTO token_usage(user_id,day,calls,prompt_tokens,
                 completion_tokens,total_tokens,updated_at)
               VALUES(?,?,1,?,?,?,?)
               ON CONFLICT(user_id,day) DO UPDATE SET
                 calls = token_usage.calls + 1,
                 prompt_tokens = token_usage.prompt_tokens + excluded.prompt_tokens,
                 completion_tokens = token_usage.completion_tokens + excluded.completion_tokens,
                 total_tokens = token_usage.total_tokens + excluded.total_tokens,
                 updated_at = excluded.updated_at""",
            (user_id, _utc_day(), _int("prompt_tokens"), _int("completion_tokens"),
             _int("total_tokens"), now))
        con.commit()
    finally:
        con.close()


def usage_by_user() -> dict[int, dict]:
    """Token spend per account: today's bucket and the all-time total."""
    ensure_schema()
    today = _utc_day()
    con = _conn()
    try:
        rows = con.execute(
            """SELECT user_id,
                      SUM(CASE WHEN day=? THEN total_tokens ELSE 0 END) today_tokens,
                      SUM(CASE WHEN day=? THEN calls ELSE 0 END) today_calls,
                      SUM(total_tokens) total_tokens,
                      SUM(prompt_tokens) prompt_tokens,
                      SUM(completion_tokens) completion_tokens,
                      SUM(calls) calls
               FROM token_usage GROUP BY user_id""", (today, today)).fetchall()
    finally:
        con.close()
    return {
        r["user_id"]: {
            "today_tokens": r["today_tokens"] or 0,
            "today_calls": r["today_calls"] or 0,
            "total_tokens": r["total_tokens"] or 0,
            "prompt_tokens": r["prompt_tokens"] or 0,
            "completion_tokens": r["completion_tokens"] or 0,
            "calls": r["calls"] or 0,
        }
        for r in rows
    }


# ── repair planning (the deterministic half of the run — no LLM) ─────────────
def _case_collision_victims(con: sqlite3.Connection) -> list[str]:
    """Lemmas whose card is a byte-identical copy of another spelling's card.

    That is the fingerprint of the folded-lookup bug: the model answered both
    halves of the pair, one answer was dropped, and both lemmas were saved with
    the survivor. Verified against the live base — of 1081 case pairs, all 635
    with identical cards were sent in ONE batch and all 446 split across batches
    were correct — so identical data is a precise marker, not a heuristic.
    """
    groups: dict[str, list[str]] = {}
    for (lemma,) in con.execute("SELECT lemma FROM cards"):
        groups.setdefault(lemma.lower(), []).append(lemma)
    victims: list[str] = []
    for spellings in groups.values():
        if len(spellings) < 2:
            continue
        qs = ",".join("?" * len(spellings))
        rows = con.execute(
            f"SELECT lemma, data FROM cards WHERE lemma IN ({qs})", spellings
        ).fetchall()
        if len({r["data"] for r in rows}) == 1:
            victims.extend(r["lemma"] for r in rows)
    return victims


def plan_repairs() -> dict:
    """Queue the known-bad cards for re-enrichment and backfill `cards.zipf`.

    Runs on every start and must be idempotent, which here means *self-limiting*:
    a word is only ever tagged into a repair phase while it is still untagged
    (`phase` NULL/backfill). Once tagged it keeps that tag whatever the outcome,
    so a repair that the model refuses, or that legitimately produces identical
    cards again, is attempted once and never loops. Cheap, deterministic, no LLM.
    """
    ensure_schema()
    con = _conn()
    try:
        # Frequency for cards enriched before the column existed.
        #
        # The EXISTS guard is what makes this terminate. A renamed card (Schluss)
        # has no vocab.db row, so the subquery yields NULL and its zipf stays
        # NULL — without the guard the UPDATE would "fill" it on every single run,
        # keep reporting rows filled, and trigger a full 64k mirror replay at
        # every start, forever. Those cards sort last, which is right: an
        # obsolete-spelling entry is not a high-frequency headword.
        zipf_filled = 0
        if VOCAB_DB.exists():
            zipf_filled = con.execute(
                """UPDATE cards SET zipf =
                     (SELECT w.zipf FROM v.words w WHERE w.lemma = cards.lemma)
                   WHERE zipf IS NULL
                     AND EXISTS (SELECT 1 FROM v.words w
                                 WHERE w.lemma = cards.lemma
                                   AND w.zipf IS NOT NULL)""").rowcount
        untagged = f"COALESCE(phase,'{BACKFILL}') = '{BACKFILL}'"
        victims = [
            l for l in _case_collision_victims(con)
            if con.execute(
                f"SELECT 1 FROM word_status WHERE lemma=? AND {untagged}", (l,)
            ).fetchone()
        ]
        broken = [r[0] for r in con.execute(
            f"SELECT lemma FROM word_status WHERE status='failed' AND {untagged}")]
        con.commit()
    finally:
        con.close()
    # Keep the old cards live while they wait — a stale entry beats a hole.
    n_case = requeue(victims, drop_card=False, phase="repair_case")
    n_ortho = requeue(broken, drop_card=False, phase="repair_ortho")
    return {"repair_case": n_case, "repair_ortho": n_ortho, "zipf_filled": zipf_filled}


def requeue_low_confidence() -> int:
    """Requeue every low-confidence card for re-enrichment. The improved prompt
    (model-side skip + no invented readings) should now either produce a
    high-confidence card or skip the word."""
    con = _conn()
    try:
        lemmas = [r[0] for r in con.execute(
            "SELECT lemma FROM cards WHERE confidence='low'").fetchall()]
    finally:
        con.close()
    return requeue(lemmas)


def list_cards(q: str = "", confidence: str = "", topic: str = "",
               level: str = "", limit: int = 40, offset: int = 0) -> dict:
    """Browse enriched cards (the OUTPUT the app shows). Returns
    {items, total} for the given filter, newest first."""
    ensure_schema()
    con = _conn()
    try:
        where, params = [], []
        if q:
            where.append("lemma LIKE ?")
            params.append(q + "%")
        if confidence in ("high", "low"):
            where.append("confidence = ?")
            params.append(confidence)
        if topic:
            where.append("topic = ?")
            params.append(topic)
        if level:
            where.append("level = ?")
            params.append(level)
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        total = con.execute(
            "SELECT COUNT(*) FROM cards" + clause, params).fetchone()[0]
        rows = con.execute(
            "SELECT lemma, level, topic, pos, article, ru, confidence, register, "
            "data, model FROM cards" + clause +
            " ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [*params, max(1, min(int(limit), 200)), max(0, int(offset))],
        ).fetchall()
    finally:
        con.close()
    items = []
    for r in rows:
        try:
            data = json.loads(r["data"]) if r["data"] else {}
        except json.JSONDecodeError:
            data = {}
        items.append({
            "lemma": r["lemma"], "level": r["level"], "topic": r["topic"],
            "pos": r["pos"], "article": r["article"], "ru": r["ru"],
            "confidence": r["confidence"], "register": r["register"],
            "model": r["model"], **data,
        })
    return {"items": items, "total": total}


def get_card(lemma: str) -> dict | None:
    con = _conn()
    try:
        r = con.execute(
            "SELECT lemma, level, topic, pos, article, ru, confidence, register, "
            "data, model, prompt_version FROM cards WHERE lemma=?",
            (lemma,)).fetchone()
    finally:
        con.close()
    if not r:
        return None
    try:
        data = json.loads(r["data"]) if r["data"] else {}
    except json.JSONDecodeError:
        data = {}
    return {"lemma": r["lemma"], "level": r["level"], "topic": r["topic"],
            "pos": r["pos"], "article": r["article"], "ru": r["ru"],
            "confidence": r["confidence"], "register": r["register"],
            "model": r["model"], "prompt_version": r["prompt_version"], **data}


def release(lemmas: list[str]) -> int:
    """Free a lease without counting an attempt (transport failure — not the
    word's fault). Only affects still-raw rows."""
    if not lemmas:
        return 0
    now = time.time()
    con = _conn()
    try:
        qs = ",".join("?" * len(lemmas))
        cur = con.execute(
            f"UPDATE word_status SET lease_owner=NULL, lease_at=NULL, updated_at=? "
            f"WHERE status='raw' AND lemma IN ({qs})",
            [now, *lemmas])
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def progress() -> dict:
    ensure_schema()
    if not VOCAB_DB.exists():
        return {"exists": False}
    fresh = time.time() - STALE_LEASE
    con = _conn()
    try:
        total = con.execute("SELECT COUNT(*) FROM v.words").fetchone()[0]
        junk = con.execute(
            f"SELECT COUNT(*) FROM v.words w WHERE {JUNK_SQL}").fetchone()[0]
        done = con.execute(
            "SELECT COUNT(*) FROM word_status WHERE status='done'").fetchone()[0]
        failed = con.execute(
            "SELECT COUNT(*) FROM word_status WHERE status='failed'").fetchone()[0]
        skipped = con.execute(
            "SELECT COUNT(*) FROM word_status WHERE status='skipped'").fetchone()[0]
        # Authoritative "still to enrich": real (non-junk) words with no terminal
        # status. Computed in SQL so junk-that's-also-skipped isn't double-counted.
        remaining = con.execute(
            f"""SELECT COUNT(*) FROM v.words w
                LEFT JOIN word_status ws ON ws.lemma=w.lemma
                WHERE NOT {JUNK_SQL}
                  AND COALESCE(ws.status,'raw') NOT IN ('done','failed','skipped')"""
        ).fetchone()[0]
        in_flight = con.execute(
            "SELECT COUNT(*) FROM word_status WHERE status='raw' AND lease_at>=?",
            (fresh,)).fetchone()[0]
        by_level = {
            r["level"]: {"total": r["t"], "done": r["d"] or 0}
            for r in con.execute(
                "SELECT w.level, COUNT(*) t, "
                "SUM(CASE WHEN ws.status='done' THEN 1 ELSE 0 END) d "
                "FROM v.words w LEFT JOIN word_status ws ON ws.lemma=w.lemma "
                "GROUP BY w.level")
        }
        recent = [
            {"lemma": r["lemma"], "ru": r["ru"], "topic": r["topic"],
             "confidence": r["confidence"]}
            for r in con.execute(
                "SELECT lemma, ru, topic, confidence FROM cards "
                "ORDER BY created_at DESC LIMIT 12")
        ]
        low_conf = con.execute(
            "SELECT COUNT(*) FROM cards WHERE confidence='low'").fetchone()[0]
        # Work still outstanding per phase, and how big each phase was planned to
        # be. `claim` serves the highest-priority phase that still has any, so the
        # first row with remaining>0 IS what every worker is currently doing.
        left = {
            r["ph"]: r["n"]
            for r in con.execute(
                f"""SELECT COALESCE(ws.phase,'{BACKFILL}') ph, COUNT(*) n
                    FROM v.words w LEFT JOIN word_status ws ON ws.lemma=w.lemma
                    WHERE NOT {JUNK_SQL}
                      AND COALESCE(ws.status,'raw') NOT IN ('done','failed','skipped')
                    GROUP BY ph""")
        }
        planned = {
            r["phase"]: r["n"]
            for r in con.execute(
                "SELECT phase, COUNT(*) n FROM word_status "
                "WHERE phase IS NOT NULL GROUP BY phase")
        }
    finally:
        con.close()
    # `enrichable` excludes junk we never send; progress is measured against it.
    enrichable = max(0, total - junk)
    # A repair phase is a fixed planned set, so it can show "3 of 1274 left". The
    # backfill has no planned size of its own (its words are simply untagged), and
    # its progress is the global bar — so it reports no total.
    phases = [
        {
            "name": name,
            "title": title,
            "remaining": left.get(name, 0),
            "total": planned.get(name) if name != BACKFILL else None,
        }
        for name, title in PHASES
    ]
    current = next((p for p in phases if p["remaining"] > 0), None)
    return {
        "exists": True, "total": total, "enrichable": enrichable, "junk": junk,
        "enriched": done, "failed": failed, "skipped": skipped,
        "remaining": remaining, "in_flight": in_flight,
        "pct": round(100 * done / enrichable, 2) if enrichable else 0,
        "by_level": by_level, "recent": recent, "low_confidence": low_conf,
        "phases": phases,
        "phase": current["name"] if current else None,
        "phase_title": current["title"] if current else None,
    }
