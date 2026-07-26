#!/usr/bin/env python
"""Покрытие внешнего корпуса — единственная метрика качества базы, которая
меряется НЕ на самой базе.

Зачем этот файл существует. 19 июля замер на 18 статьях de.wikipedia по темам
Goethe показал, что **82 % промахов — от источника, а не от обогащения**, и
развернул приоритеты целиком: чинить надо было вход, а не модель. Тем же
замером потом подтвердили, что вливание слов дало 72.3 → 76.4 % по токенам.

И этот замер потерялся. `PLANS.md` до сих пор ссылается на «coverage.py /
coverage2.py (в скретчпаде)» — скретчпад давно стёрт, корпус нигде не записан,
и следующий замер было бы не с чем сравнивать. Файл возвращает метрику в
репозиторий: корпус зафиксирован списком ниже, прогон воспроизводим.

Запуск:

    uv run python backend/scripts/coverage.py
    uv run python backend/scripts/coverage.py --json      # для CI/истории
    uv run python backend/scripts/coverage.py --min-zipf 3.0

Ноль вызовов модели, ноль записи в БД: только чтение.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Корпус. Это НЕ случайные статьи: темы совпадают с Goethe B2/C1 Schreiben,
# ради которых существует тренажёр. Меняя список, вы обрываете сравнимость с
# замерами 19 июля (72.3 % → 76.4 %) — тогда заводите вторую метрику, а эту
# оставьте как есть.
CORPUS = [
    "Künstliche Intelligenz", "Datenschutz", "Soziales Netzwerk (Internet)",
    "Klimawandel", "Digitalisierung", "Migration (Soziologie)",
    "Globalisierung", "Bildung", "Gesundheitswesen", "Nachhaltigkeit",
    "Arbeitswelt", "Urbanisierung", "Erneuerbare Energien",
    "Ehrenamt", "Massenmedien", "Konsumgesellschaft",
    "Gleichberechtigung", "Demografischer Wandel",
]

# Action API с `explaintext`: отдаёт ПОЛНЫЙ текст статьи. REST-эндпоинт
# `/api/rest_v1/page/plain/` не существует (404), а `page/summary` вернул бы
# только первый абзац — на нём замер потерял бы смысл.
WIKI_API = "https://de.wikipedia.org/w/api.php"
CACHE = REPO / "backend" / "data" / "coverage-corpus"

# Немецкое слово: буквы плюс умляуты и ß, минимум две буквы.
WORD = re.compile(r"[A-Za-zÄÖÜäöüß]{2,}")

# Служебные части речи и английские вкрапления, которые замер 19 июля отдельно
# отметил как искажающие картину: их отсутствие в словаре — не пробел базы.
NOISE = {
    "the", "of", "and", "to", "in", "for", "on", "is", "with", "by", "as", "at",
    "usw", "bzw", "ca", "vgl", "ebd", "ff", "bspw", "ggf", "zb", "dh",
}


def _fetch(title: str) -> str:
    path = CACHE / (re.sub(r"[^\w]+", "_", title) + ".txt")
    if path.exists():
        return path.read_text(encoding="utf-8")
    query = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "explaintext": "1",
        "redirects": "1", "format": "json", "formatversion": "2", "titles": title,
    })
    req = urllib.request.Request(
        f"{WIKI_API}?{query}",
        headers={"User-Agent": "deutsch-essay-trainer/coverage (local measurement)"},
    )
    # Wikipedia отдаёт 429 на быструю серию запросов. Корпус тянется один раз
    # и потом лежит в кэше, поэтому спешить некуда: пауза дешевле провала.
    payload = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                payload = json.loads(r.read().decode("utf-8", "replace"))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(2 ** attempt)
    time.sleep(1.0)
    pages = payload.get("query", {}).get("pages", [])
    if not pages or "extract" not in pages[0]:
        sys.exit(f"не удалось получить текст статьи «{title}» — проверьте название в CORPUS")
    text = pages[0]["extract"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def _known_lemmas(db: Path) -> set[str]:
    """Все леммы с готовой карточкой.

    ⚠️ Падаем, если карточек ноль. Рядом с боевыми БД лежат заглушки
    `app/vocab/*.db`, и путь по умолчанию резолвится именно в них — скрипт
    отработал бы «успешно» и отрапортовал 0 % покрытия, что выглядит как
    катастрофа в базе, а на деле означает, что читали не тот файл. Признак
    подмены — ноль в ЗНАМЕНАТЕЛЕ.
    """
    if not db.exists():
        sys.exit(f"нет БД: {db}\nукажите --enrich-db или задайте ENRICHMENT_DB")
    con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    try:
        lemmas = {row[0] for row in con.execute("SELECT lemma FROM cards")}
    finally:
        con.close()
    if not lemmas:
        sys.exit(
            f"в {db} ноль карточек — почти наверняка это заглушка, а не боевая база.\n"
            f"Боевая: backend/app/vocab/vocab_data/enrichment.db"
        )
    return lemmas


def _covered(token: str, known: set[str]) -> bool:
    return (
        token in known
        or token.lower() in known
        or token.capitalize() in known
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--enrich-db",
        type=Path,
        default=Path(os.environ.get("ENRICHMENT_DB", REPO / "backend/app/vocab/vocab_data/enrichment.db")),
    )
    ap.add_argument("--json", action="store_true", help="машиночитаемый вывод")
    ap.add_argument("--top-misses", type=int, default=25)
    args = ap.parse_args()

    known = _known_lemmas(args.enrich_db)

    tokens: Counter[str] = Counter()
    for title in CORPUS:
        tokens.update(WORD.findall(_fetch(title)))

    significant = {t: n for t, n in tokens.items() if t.lower() not in NOISE}
    total_tokens = sum(significant.values())
    hit_tokens = sum(n for t, n in significant.items() if _covered(t, known))
    types = set(significant)
    hit_types = {t for t in types if _covered(t, known)}
    misses = Counter({t: significant[t] for t in types - hit_types})

    result = {
        "corpus_articles": len(CORPUS),
        "cards_in_db": len(known),
        "tokens_total": total_tokens,
        "tokens_covered": hit_tokens,
        "coverage_tokens_pct": round(100 * hit_tokens / total_tokens, 1) if total_tokens else 0.0,
        "types_total": len(types),
        "types_covered": len(hit_types),
        "coverage_types_pct": round(100 * len(hit_types) / len(types), 1) if types else 0.0,
        "top_misses": misses.most_common(args.top_misses),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"БД:      {args.enrich_db}")
    print(f"карточек: {result['cards_in_db']:,}".replace(",", " "))
    print(f"корпус:   {result['corpus_articles']} статей de.wikipedia по темам Goethe")
    print()
    print(f"покрытие по токенам: {result['coverage_tokens_pct']:5.1f} %  "
          f"({result['tokens_covered']:,} из {result['tokens_total']:,})".replace(",", " "))
    print(f"покрытие по типам:   {result['coverage_types_pct']:5.1f} %  "
          f"({result['types_covered']:,} из {result['types_total']:,})".replace(",", " "))
    print()
    print(f"чаще всего промахиваемся ({args.top_misses}):")
    for word, n in result["top_misses"]:
        print(f"  {n:5}  {word}")
    print()
    print("⚠️  С числами 19 июля (72.3 → 76.4 %) это НЕ сравнивать: там был свой")
    print("    список статей и своя токенизация. Здесь новая базовая точка —")
    print("    сравнивать имеет смысл только последующие прогоны этого файла.")
    print()
    print("⚠️  Замер сверяет леммы, а не ходит в поиск. Словоформы (`einem`,")
    print("    `ihrer`, `wurde`) считаются промахом, хотя поиск находит их")
    print("    триграммами. Поэтому «по типам» систематически занижено.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
