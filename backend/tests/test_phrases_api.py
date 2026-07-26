"""Клише для эссе — то, что осталось живого от `/api/phrases`.

`GET /api/phrases` (без `/templates`) удалён 2026-07-26 вместе с роутером
`/api/words`: во фронте его не звал никто. А `GET /api/phrases/templates` —
единственный источник 1 748 шаблонов на странице Schreiben, тот самый, ради
которого чинили выдачу (`info/PLANS.md`, пункт F), — не был покрыт ни одним
тестом. Здесь закрывается именно он.

Шаблоны проверяются на Postgres, а не на sqlite: `list_templates` стоит на
`DISTINCT ON`, которого в SQLite нет вовсе. Фикстура `pg_client` пропускает
тест, если Postgres недоступен.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import Phrase


def _phrase(
    text_de: str,
    *,
    part: str = "einleitung",
    topic: str | None = "technologie",
    level: str = "B1",
) -> Phrase:
    return Phrase(
        text_de=text_de,
        translation_ru="перевод",
        essay_part=part,
        topic=topic,
        level=level,
    )


async def test_templates_collapse_repeats_but_keep_both_parts(pg_client, pg_session):
    """Дедупликация идёт ВНУТРИ части, а не по всей таблице.

    Таблица держит шаблон по строке на каждую тему, поэтому «Daraus ergibt
    sich die Frage, ob ...» лежит там 120 раз — выдать его надо один раз. Но он
    же числится и во вступлении, и в аргументе, и оба раза верно: глобальный
    DISTINCT отдавал текст одной части и молча укорачивал список другой
    (einleitung возвращал 366 строк вместо 374).
    """
    pg_session.add_all([
        _phrase("Daraus ergibt sich die Frage, ob ...", topic="technologie"),
        _phrase("Daraus ergibt sich die Frage, ob ...", topic="umwelt"),
        _phrase("Daraus ergibt sich die Frage, ob ...", part="argument", topic="umwelt"),
    ])
    await pg_session.commit()

    einleitung = (await pg_client.get("/api/phrases/templates?part=einleitung")).json()
    argument = (await pg_client.get("/api/phrases/templates?part=argument")).json()

    assert [p["text_de"] for p in einleitung] == ["Daraus ergibt sich die Frage, ob ..."]
    assert [p["text_de"] for p in argument] == ["Daraus ergibt sich die Frage, ob ..."]


async def test_templates_leave_out_finished_sentences(pg_client, pg_session):
    """Признак шаблона — многоточие, а не повторяемость.

    Рядом с шаблонами в той же таблице лежат содержательные предложения под
    конкретную тему («In Schweden wurde Mikroplastik 2018 verboten»). Их 93 из
    1 806, и в чужое эссе они не пересаживаются.
    """
    pg_session.add_all([
        _phrase("Ich bin der Meinung, dass ..."),
        _phrase("In Schweden wurde Mikroplastik im Jahr 2018 verboten."),
    ])
    await pg_session.commit()

    texts = [p["text_de"] for p in (await pg_client.get("/api/phrases/templates")).json()]
    assert texts == ["Ich bin der Meinung, dass ..."]


async def test_templates_come_shortest_first(pg_client, pg_session):
    """Длинные зачины называют свою исходную тему и никуда не пересаживаются."""
    pg_session.add_all([
        _phrase(
            "Angesichts der rasanten Fortschritte im Bereich der künstlichen "
            "Intelligenz rückt die Frage in den Fokus, ob ..."
        ),
        _phrase("Am Anfang steht ..."),
    ])
    await pg_session.commit()

    texts = [p["text_de"] for p in (await pg_client.get("/api/phrases/templates")).json()]
    assert texts[0] == "Am Anfang steht ..."


async def test_phrase_known_toggle(client, db_session):
    """Флаг «знаю» пишется и читается обратно.

    Идёт по sqlite и берёт id прямо из БД: единственный роут, который отдавал
    id клише без `DISTINCT ON`, был `GET /api/phrases` — он удалён.
    """
    db_session.add(_phrase("Ich bin der Meinung, dass ..."))
    await db_session.commit()
    phrase = (await db_session.execute(select(Phrase))).scalars().first()

    res = await client.post(f"/api/phrases/{phrase.id}/known", json={"known": True})
    assert res.status_code == 200
    assert res.json() == {"phrase_id": phrase.id, "known": True}
