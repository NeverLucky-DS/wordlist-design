#!/usr/bin/env python3
"""DB audit — заполненность полей слов и клише в боевой БД.

Запуск (из контейнера backend или локально с доступом к Postgres):

    # вариант 1: внутри docker
    docker compose exec backend python audit_db.py

    # вариант 2: локально, указав URL
    DATABASE_URL="postgresql://wordlist:wordlist@localhost:5432/wordlist" python audit_db.py

Работает и с sqlite (DATABASE_URL=sqlite:///./data/app.db) — для проверки на снимке.
Только читает. Ничего не меняет.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

URL = os.environ.get("DATABASE_URL", "").strip()
if not URL:
    # дефолт — попробуем боевой postgres из docker-compose
    URL = "postgresql://wordlist:wordlist@localhost:5432/wordlist"

# нормализуем async-драйверы к sync
URL = URL.replace("+asyncpg", "").replace("+aiosqlite", "").replace("+psycopg2", "")

IS_SQLITE = URL.startswith("sqlite")


def connect():
    if IS_SQLITE:
        import sqlite3
        path = URL.split("///")[-1]
        con = sqlite3.connect(path)
        con.row_factory = sqlite3.Row
        return con, "sqlite"
    try:
        import psycopg2
        import psycopg2.extras
        con = psycopg2.connect(URL)
        return con, "pg"
    except ImportError:
        print("psycopg2 не установлен. В контейнере backend он есть; "
              "или: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)


def rows(cur, sql):
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    for r in cur.fetchall():
        yield dict(zip(cols, r)) if not IS_SQLITE else dict(r)


def as_obj(v):
    """grammar_data/examples могут быть JSON-строкой (sqlite) или dict (pg JSONB)."""
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return None


def empty(v):
    return v is None or v == "" or v == {} or v == [] or (isinstance(v, str) and not v.strip())


def main():
    con, kind = connect()
    cur = con.cursor()

    word_rows = list(rows(cur, "SELECT * FROM words"))
    total = len(word_rows)
    print(f"\n{'='*60}\nБД: {kind}  |  слов всего: {total}\n{'='*60}")

    by_type = Counter(r["word_type"] for r in word_rows)
    by_source = Counter(r.get("source") for r in word_rows)
    by_level = Counter(r.get("level") for r in word_rows)
    print("По типу:   ", dict(by_type))
    print("По источн.:", dict(by_source))
    print("По уровню: ", dict(by_level))

    stat = Counter()
    decl_shapes = Counter()
    ex_origin = Counter()
    ex_count = Counter()
    bold_md = 0      # примеры с **markdown**
    bold_html = 0    # примеры с <b>
    bad_lemma = []   # лемма с артиклем внутри / странная

    for r in word_rows:
        wtype = r["word_type"]
        g = as_obj(r.get("grammar_data")) or {}
        ex = as_obj(r.get("examples")) or []

        if empty(r.get("translation_ru")):
            stat["пустой перевод RU"] += 1
        if empty(r.get("level")):
            stat["пустой уровень"] += 1
        if wtype == "noun" and empty(r.get("article")):
            stat["сущ. без артикля"] += 1

        # лемма
        german = (r.get("german") or "")
        if german[:4].lower() in ("der ", "die ", "das "):
            bad_lemma.append(german)

        # grammar
        if not g:
            stat["нет grammar_data"] += 1
        else:
            if empty(g.get("rektion")):
                stat["пустой rektion"] += 1
            if empty(g.get("ready_phrase")):
                stat["пустой ready_phrase"] += 1
            decl = g.get("declension") or {}
            if empty(decl):
                stat["пустое склонение"] += 1
            else:
                decl_shapes[tuple(sorted(str(k) for k in decl.keys()))[:6]] += 1

        # examples
        ex_count[len(ex)] += 1
        if not ex:
            stat["нет примеров"] += 1
        elif len(ex) < 2:
            stat["<2 примеров"] += 1
        for e in ex:
            txt = e.get("text_de", "") if isinstance(e, dict) else str(e)
            if isinstance(e, dict) and e.get("is_ai"):
                ex_origin["ai"] += 1
            else:
                ex_origin["real"] += 1
            if "**" in txt:
                bold_md += 1
            if "<b>" in txt:
                bold_html += 1

    print(f"\n{'-'*60}\nПУСТЫЕ / ПРОБЛЕМНЫЕ ПОЛЯ (из {total} слов)\n{'-'*60}")
    for k, v in sorted(stat.items(), key=lambda x: -x[1]):
        print(f"  {k:28} {v:5}  ({100*v//max(total,1)}%)")

    print(f"\nПримеры: распределение количества: {dict(sorted(ex_count.items()))}")
    print(f"Примеры: происхождение: {dict(ex_origin)}")
    print(f"Примеры с **markdown**: {bold_md}   с <b>: {bold_html}")

    print(f"\nФорматы ключей склонения (топ-10) — должен быть ОДИН:")
    for shape, n in decl_shapes.most_common(10):
        print(f"  {n:4}  {list(shape)}")

    if bad_lemma:
        print(f"\nЛеммы с артиклем внутри ({len(bad_lemma)}): {bad_lemma[:20]}")

    # по темам
    print(f"\n{'-'*60}\nПО ТЕМАМ\n{'-'*60}")
    topic_rows = list(rows(cur, """
        SELECT wt.topic, COUNT(*) n
        FROM word_topics wt GROUP BY wt.topic ORDER BY n DESC
    """))
    for t in topic_rows:
        print(f"  {str(t['topic']):32} {t['n']:4} слов")

    # клише
    try:
        ph = list(rows(cur, "SELECT topic, COUNT(*) n FROM phrases GROUP BY topic"))
        print(f"\nКЛИШЕ (Redemittel) по темам:")
        for p in ph:
            print(f"  {str(p['topic']):32} {p['n']:4}")
        ph_empty_ru = list(rows(cur,
            "SELECT COUNT(*) n FROM phrases WHERE translation_ru IS NULL OR translation_ru=''"))
        print(f"  клише без перевода RU: {ph_empty_ru[0]['n']}")
    except Exception as e:
        print("phrases:", e)

    con.close()
    print(f"\n{'='*60}\nГотово. Скопируй вывод и пришли мне.\n{'='*60}")


if __name__ == "__main__":
    main()
