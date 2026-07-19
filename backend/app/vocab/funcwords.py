"""Closed-class words the enrichment model refuses by design.

Measured 2026-07-19 against an external corpus: `das` had a card but `der`,
`die`, `den`, `dem` and `des` did not. `die/den/dem` came back `skipped`,
`der/des` went `failed` after three attempts — both statuses are terminal, so
the most frequent words in German (`die` sits at zipf 7.48) were gone for good.
The same hole swallowed every contracted preposition: `im`, `am`, `zum`, `zur`,
`vom`, `beim`, `ins`.

The cause is the Wortform rule in the prompt, and the rule is *right*: `die` is
a form of `der`, `im` is `in` + `dem`. It correctly parks `ist`, `hat`, `war`
and `meine` in `skipped`, where their base lemmas already carry the card. The
rule only misfires on the closed class, where the "base form" is a paradigm
cell nobody looks up and the contraction is a thing learners must simply know —
"im = in dem" is A1 grammar in every textbook, not something derivable.

So these are written by hand rather than asked for again. The set is closed and
finite: twenty-five entries, no model call, no tokens. Fighting the prompt to
extract them would cost tokens and damage a rule that is otherwise doing its
job.

Cards are filed with model='handwritten' so they can always be told apart from
generated ones, and re-running `seed()` just rewrites the same rows.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

MODEL = "handwritten"
TOPIC = "allgemein_funktionswoerter"


def _card(pos: str, ru: str, ru_all: list[str], de: str, examples: list[tuple[str, str]],
          *, article: str | None = None, grammar: dict | None = None,
          synonyms: list[str] | None = None,
          collocations: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema": 1, "pos": pos, "article": article, "ru": ru, "ru_all": ru_all,
        "definition_de": de, "grammar": grammar or {}, "rektion": "",
        "synonyms": synonyms or [], "collocations": collocations or [],
        "topic": TOPIC, "register": "neutral", "confidence": "high",
        "examples": [{"de": d, "ru": r} for d, r in examples],
    }


def _contraction(lemma: str, prep: str, art: str, case: str, ru: str,
                 examples: list[tuple[str, str]]) -> dict[str, Any]:
    """A preposition fused with an article — 'im' = 'in dem'.

    Spelled out in `grammar.zusammensetzung` because the whole point for a
    learner is seeing which two words are inside, and in `rektion` because the
    case is what picks the contraction in the first place.
    """
    card = _card(
        "other", ru, [ru],
        f"Verschmelzung von „{prep}“ und „{art}“ ({case}).",
        examples,
        grammar={"zusammensetzung": f"{prep} + {art}", "kasus": case},
        synonyms=[f"{prep} {art}"],
    )
    card["rektion"] = f"{prep} + {case}"
    return card


CARDS: dict[str, dict[str, Any]] = {
    # ── definite article ─────────────────────────────────────────────────────
    "der": _card(
        "other", "определённый артикль (мужской род)",
        ["определённый артикль (мужской род)", "который", "этот"],
        "Bestimmter Artikel für maskuline Substantive im Nominativ Singular; "
        "außerdem Dativ und Genitiv Singular femininum sowie Genitiv Plural.",
        [("**Der** Mann liest ein Buch.", "Этот мужчина читает книгу."),
         ("Ich helfe **der** Frau.", "Я помогаю этой женщине."),
         ("Das ist **der** Anfang **der** Geschichte.", "Это начало истории.")],
        grammar={"deklination": "der / des / dem / den (m. Sg.)"},
        synonyms=["dieser", "jener"],
        collocations=["der Mann", "der Tag", "der Grund"]),
    "die": _card(
        "other", "определённый артикль (женский род и мн. ч.)",
        ["определённый артикль (женский род)", "определённый артикль (множественное число)",
         "которая", "которые"],
        "Bestimmter Artikel für feminine Substantive und für den Plural aller "
        "Geschlechter im Nominativ und Akkusativ.",
        [("**Die** Frau arbeitet im Krankenhaus.", "Эта женщина работает в больнице."),
         ("**Die** Kinder spielen draußen.", "Дети играют на улице."),
         ("Ich kenne **die** Antwort nicht.", "Я не знаю ответа.")],
        grammar={"deklination": "die / der / der / die (f. Sg.); die / der / den / die (Pl.)"},
        synonyms=["diese", "jene"],
        collocations=["die Frage", "die Menschen", "die Möglichkeit"]),
    "den": _card(
        "other", "определённый артикль (вин. п. м. р., дат. п. мн. ч.)",
        ["определённый артикль (винительный падеж, мужской род)",
         "определённый артикль (дательный падеж, множественное число)"],
        "Bestimmter Artikel: Akkusativ Singular maskulinum sowie Dativ Plural.",
        [("Ich sehe **den** Hund.", "Я вижу собаку."),
         ("Wir danken **den** Gästen.", "Мы благодарим гостей."),
         ("Er stellt **den** Stuhl an **den** Tisch.", "Он ставит стул к столу.")],
        grammar={"kasus": "Akkusativ Sg. m. / Dativ Pl."},
        collocations=["den ganzen Tag", "den Menschen", "den Eindruck"]),
    "dem": _card(
        "other", "определённый артикль (дат. п. м. и ср. р.)",
        ["определённый артикль (дательный падеж, мужской род)",
         "определённый артикль (дательный падеж, средний род)"],
        "Bestimmter Artikel im Dativ Singular für maskuline und neutrale Substantive.",
        [("Ich gebe **dem** Kind einen Apfel.", "Я даю ребёнку яблоко."),
         ("Sie spricht mit **dem** Lehrer.", "Она говорит с учителем."),
         ("Nach **dem** Essen gehen wir spazieren.", "После еды мы идём гулять.")],
        grammar={"kasus": "Dativ Sg. m./n."},
        collocations=["mit dem Auto", "nach dem Essen", "aus dem Haus"]),
    "des": _card(
        "other", "определённый артикль (род. п. м. и ср. р.)",
        ["определённый артикль (родительный падеж, мужской род)",
         "определённый артикль (родительный падеж, средний род)"],
        "Bestimmter Artikel im Genitiv Singular für maskuline und neutrale "
        "Substantive; das Substantiv erhält die Endung -s oder -es.",
        [("Das Dach **des** Hauses ist neu.", "Крыша дома новая."),
         ("Die Rolle **des** Staates wird diskutiert.", "Роль государства обсуждается."),
         ("Am Ende **des** Tages zählt das Ergebnis.", "В конце дня важен результат.")],
        grammar={"kasus": "Genitiv Sg. m./n.", "hinweis": "Substantiv + -s / -es"},
        collocations=["des Landes", "des Menschen", "des Jahres"]),

    # ── preposition + article contractions ───────────────────────────────────
    "im": _contraction("im", "in", "dem", "Dativ", "в (слитно: in + dem)",
                       [("Wir wohnen **im** Zentrum.", "Мы живём в центре."),
                        ("**Im** Sommer fahren wir ans Meer.", "Летом мы едем на море."),
                        ("Das steht **im** Text.", "Это написано в тексте.")]),
    "am": _contraction("am", "an", "dem", "Dativ", "у, на, в (слитно: an + dem)",
                       [("Wir sitzen **am** Tisch.", "Мы сидим за столом."),
                        ("**Am** Montag beginnt der Kurs.", "В понедельник начинается курс."),
                        ("Sie wartet **am** Bahnhof.", "Она ждёт на вокзале.")]),
    "zum": _contraction("zum", "zu", "dem", "Dativ", "к, на (слитно: zu + dem)",
                        [("Ich gehe **zum** Arzt.", "Я иду к врачу."),
                         ("**Zum** Glück hat es geklappt.", "К счастью, получилось."),
                         ("Wir fahren **zum** Bahnhof.", "Мы едем на вокзал.")]),
    "zur": _contraction("zur", "zu", "der", "Dativ", "к, на (слитно: zu + der)",
                        [("Sie geht **zur** Schule.", "Она идёт в школу."),
                         ("**Zur** Zeit bin ich beschäftigt.", "В данный момент я занят."),
                         ("Das führt **zur** Frage, was zu tun ist.",
                          "Это приводит к вопросу, что делать.")]),
    "vom": _contraction("vom", "von", "dem", "Dativ", "от, с (слитно: von + dem)",
                        [("Ich komme **vom** Arzt.", "Я иду от врача."),
                         ("Das hängt **vom** Wetter ab.", "Это зависит от погоды."),
                         ("**Vom** Bahnhof sind es zehn Minuten.",
                          "От вокзала это десять минут.")]),
    "beim": _contraction("beim", "bei", "dem", "Dativ", "у, при, во время (слитно: bei + dem)",
                         [("Ich war **beim** Zahnarzt.", "Я был у зубного врача."),
                          ("**Beim** Lesen schlafe ich ein.", "При чтении я засыпаю."),
                          ("Er hilft mir **beim** Umzug.", "Он помогает мне с переездом.")]),
    "ins": _contraction("ins", "in", "das", "Akkusativ", "в (слитно: in + das)",
                        [("Wir gehen **ins** Kino.", "Мы идём в кино."),
                         ("Sie springt **ins** Wasser.", "Она прыгает в воду."),
                         ("Das geht mir **ins** Ohr.", "Это мне запоминается.")]),
    "ans": _contraction("ans", "an", "das", "Akkusativ", "к, на (слитно: an + das)",
                        [("Wir fahren **ans** Meer.", "Мы едем на море."),
                         ("Er geht **ans** Fenster.", "Он подходит к окну."),
                         ("Denk **ans** Wesentliche.", "Думай о главном.")]),
    "aufs": _contraction("aufs", "auf", "das", "Akkusativ", "на (слитно: auf + das)",
                         [("Er legt das Buch **aufs** Regal.", "Он кладёт книгу на полку."),
                          ("Wir freuen uns **aufs** Wochenende.", "Мы ждём выходных."),
                          ("Das trifft **aufs** Genaueste zu.", "Это совершенно точно.")]),
    "fürs": _contraction("fürs", "für", "das", "Akkusativ", "для (слитно: für + das)",
                         [("Das ist **fürs** Kind.", "Это для ребёнка."),
                          ("**Fürs** Erste reicht das.", "На первое время этого хватит."),
                          ("Er spart **fürs** Studium.", "Он копит на учёбу.")]),
    "durchs": _contraction("durchs", "durch", "das", "Akkusativ", "через, сквозь (слитно: durch + das)",
                           [("Wir gehen **durchs** Tor.", "Мы идём через ворота."),
                            ("Der Wind weht **durchs** Fenster.", "Ветер дует через окно."),
                            ("Sie kommt gut **durchs** Leben.", "Она хорошо справляется по жизни.")]),
    "ums": _contraction("ums", "um", "das", "Akkusativ", "вокруг, около (слитно: um + das)",
                        [("Wir gehen **ums** Haus.", "Мы идём вокруг дома."),
                         ("Es geht **ums** Prinzip.", "Дело в принципе."),
                         ("**Ums** Verrecken nicht!", "Ни за что!")]),
    "übers": _contraction("übers", "über", "das", "Akkusativ", "над, через, о (слитно: über + das)",
                          [("Wir reden **übers** Wetter.", "Мы говорим о погоде."),
                           ("Die Brücke führt **übers** Wasser.", "Мост ведёт через воду."),
                           ("Das geht **übers** Ziel hinaus.", "Это перебор.")]),
    "unterm": _contraction("unterm", "unter", "dem", "Dativ", "под (слитно: unter + dem)",
                           [("Die Katze liegt **unterm** Tisch.", "Кошка лежит под столом."),
                            ("**Unterm** Strich bleibt wenig.", "В итоге остаётся немного."),
                            ("Er schläft **unterm** Baum.", "Он спит под деревом.")]),
    "vorm": _contraction("vorm", "vor", "dem", "Dativ", "перед (слитно: vor + dem)",
                         [("Ich warte **vorm** Haus.", "Я жду перед домом."),
                          ("Er hat Angst **vorm** Fliegen.", "Он боится летать."),
                          ("**Vorm** Essen wäscht man die Hände.", "Перед едой моют руки.")]),
    "hinterm": _contraction("hinterm", "hinter", "dem", "Dativ", "за (слитно: hinter + dem)",
                            [("Der Garten liegt **hinterm** Haus.", "Сад находится за домом."),
                             ("Er sitzt **hinterm** Steuer.", "Он сидит за рулём."),
                             ("**Hinterm** Berg wohnen auch Leute.",
                              "И за горой живут люди.")]),

    # ── pronouns the same rule swallowed ─────────────────────────────────────
    "euch": _card(
        "other", "вас, вам", ["вас", "вам", "вами", "себя (вы)"],
        "Personalpronomen der 2. Person Plural im Akkusativ und Dativ; "
        "außerdem Reflexivpronomen zu „ihr“.",
        [("Ich sehe **euch** morgen.", "Я увижу вас завтра."),
         ("Ich danke **euch** herzlich.", "Сердечно вас благодарю."),
         ("Setzt **euch** bitte.", "Садитесь, пожалуйста.")],
        grammar={"nominativ": "ihr", "kasus": "Akkusativ / Dativ Pl."},
        collocations=["bei euch", "für euch", "mit euch"]),
    "denen": _card(
        "other", "которым", ["которым", "тем"],
        "Dativ Plural des Relativ- und Demonstrativpronomens „der/die/das“.",
        [("Die Leute, **denen** wir geholfen haben, sind dankbar.",
          "Люди, которым мы помогли, благодарны."),
         ("Es gibt Gründe, aus **denen** das nicht geht.",
          "Есть причины, по которым это невозможно."),
         ("Das sind Themen, mit **denen** ich mich beschäftige.",
          "Это темы, которыми я занимаюсь.")],
        grammar={"kasus": "Dativ Pl.", "nominativ": "die"},
        collocations=["mit denen", "von denen", "unter denen"]),
    "aller": _card(
        "other", "всех, всей", ["всех", "всей", "всякий"],
        "Genitiv Plural sowie Genitiv und Dativ Singular femininum von „all“.",
        [("Die Mutter **aller** Probleme ist die Zeit.",
          "Мать всех проблем — время."),
         ("Trotz **aller** Bemühungen scheiterte der Plan.",
          "Несмотря на все усилия, план провалился."),
         ("Das liegt im Interesse **aller** Beteiligten.",
          "Это в интересах всех участников.")],
        grammar={"grundform": "all", "kasus": "Genitiv Pl. / Gen.+Dat. Sg. f."},
        collocations=["trotz aller", "vor allem aller", "aller Art"]),
    "wessen": _card(
        "other", "чей", ["чей", "чья", "чьё", "чьи"],
        "Interrogativ- und Relativpronomen im Genitiv: fragt nach dem Besitzer.",
        [("**Wessen** Buch ist das?", "Чья это книга?"),
         ("**Wessen** Idee war das?", "Чья это была идея?"),
         ("Er weiß, **wessen** Schuld es ist.", "Он знает, чья это вина.")],
        grammar={"kasus": "Genitiv", "nominativ": "wer"},
        collocations=["wessen Meinung", "wessen Schuld"]),
}


def seed(con, *, user_id: int = 0) -> dict:
    """Write the handwritten cards into `cards` and mark them done.

    Idempotent: INSERT OR REPLACE rewrites the same rows, and the status flip is
    an upsert. Existing generated cards are left alone — a lemma is only touched
    if we hold no card for it, so a later model pass that produces a real card
    for one of these wins and is never clobbered by a re-run.
    """
    from wordfreq import zipf_frequency

    now = time.time()
    written, kept = 0, 0
    for lemma, card in CARDS.items():
        have = con.execute("SELECT 1 FROM cards WHERE lemma=?", (lemma,)).fetchone()
        if have and con.execute(
                "SELECT model FROM cards WHERE lemma=?", (lemma,)).fetchone()[0] != MODEL:
            kept += 1
            continue
        con.execute(
            """INSERT OR REPLACE INTO cards(lemma,level,topic,pos,article,ru,
                 confidence,register,data,model,prompt_version,schema_version,
                 enriched_by,created_at,zipf)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (lemma, "a1", card["topic"], card["pos"], card["article"], card["ru"],
             card["confidence"], card["register"],
             json.dumps(card, ensure_ascii=False), MODEL, MODEL, 1,
             user_id, now, zipf_frequency(lemma, "de") or None))
        con.execute(
            """INSERT INTO word_status(lemma,status,attempts,lease_owner,lease_at,updated_at)
               VALUES(?, 'done', 0, NULL, NULL, ?)
               ON CONFLICT(lemma) DO UPDATE SET status='done', attempts=0,
                 lease_owner=NULL, lease_at=NULL, updated_at=excluded.updated_at""",
            (lemma, now))
        written += 1
    con.commit()
    logger.info("funcwords: wrote %d cards, kept %d generated ones", written, kept)
    return {"written": written, "kept_generated": kept, "total": len(CARDS)}
