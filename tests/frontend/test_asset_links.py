"""Целостность ссылок на ассеты — исполняемая версия ловушек 7 и 8.

`info/CRITICAL-LINKS.md` описывает две поломки как известные и ничем не
защищённые:

  7. «Удаление PNG до обновления CSS url() — мгновенно ломает фоны/маски на
     всех страницах.»
  8. «WASH filename typo — ключи жёстко привязаны к именам файлов в worte/.
     Одна опечатка = прозрачные карточки слов.»

Обе не видны ни компилятору (сборки нет), ни бэкенд-тестам, ни глазу: страница
не падает, она просто теряет фон. Единственной защитой был человек, помнящий
про документ. Этот файл превращает документ в проверку.

Что проверяется:
  * каждая локальная ссылка из *.html, css/*.css, js/*.js указывает на файл,
    который существует на диске;
  * все 15 кистей WASH лежат в worte/;
  * две копии карты WASH (words-data.js и wb-card.js) совпадают ключ в ключ.

Тест намеренно НЕ ходит в сеть и не поднимает браузер — он читает исходники.
Поэтому работает и в CI, где ни стека, ни картинок в контейнере нет.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

HTML_PAGES = ["index.html", "schreiben.html", "pipeline.html"]

# Внешнее, инлайновое и шаблонное — не файлы на диске, проверять нечего.
SKIP_PREFIXES = ("http://", "https://", "//", "data:", "mailto:", "#", "javascript:")

# url(...) в CSS: с кавычками и без.
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")
# src= / href= в HTML.
HTML_REF = re.compile(r"""(?:src|href)\s*=\s*['"]([^'"]+)['"]""")
# 'worte/Файл.png' и "images/файл.png" внутри JS-строк.
JS_ASSET = re.compile(r"""['"`]((?:\.{0,2}/)?(?:worte|images)/[^'"`]+\.(?:png|jpg|jpeg|svg|webp))['"`]""")
# Значения карты WASH: 'B1|der': 'Файл.png'
WASH_ENTRY = re.compile(r"""['"]((?:B1|B2|C1)\|(?:der|die|das|verb|adj))['"]\s*:\s*['"]([^'"]+\.png)['"]""")
# Голое имя файла без папки — папка приклеивается в рантайме:
#   const MID_LEAVES = ['roadmap-leaf-3.png', …];  leaf.src = 'images/' + …
# Такую ссылку не видит ни один поиск по «images/», и переименование файла
# ломает её молча. Тот же класс, что опечатка в WASH.
BARE_ASSET = re.compile(r"""['"]([\w][\w.-]*\.(?:png|jpg|jpeg|svg|webp))['"]""")

# Куда складываются ассеты — по этим папкам ищется голое имя.
ASSET_DIRS = ("images", "worte")


def _is_local(ref: str) -> bool:
    return bool(ref) and not ref.startswith(SKIP_PREFIXES) and "${" not in ref


def _resolve(ref: str, source: Path) -> Path:
    """Путь на диске для ссылки из `source` — ровно так, как её резолвит браузер.

    Абсолютный `/worte/x.png` — от корня сайта (= корня репозитория, именно так
    его отдаёт nginx).

    Относительный резолвится ПО-РАЗНОМУ, и это не придирка:

      * из CSS — от папки самого стайла. Отсюда грабли 2026-07-23: `--brush`
        это custom property с `url()`, браузер считает его относительно
        потребляющего стайла (`css/woerterbuch.css`), поэтому `worte/…`
        превращалось в `/css/worte/… → 404`. Путь к кистям обязан быть `/worte/`;
      * из HTML и JS — от корня сайта, потому что и то и другое исполняется в
        контексте документа. `brushOf()` в words-data.js делает это явно:
        `new URL('worte/' + f, document.baseURI)`.
    """
    ref = ref.split("?", 1)[0].split("#", 1)[0]  # срезаем cache-bust ?v=N
    if ref.startswith("/"):
        return REPO / ref.lstrip("/")
    base = source.parent if source.suffix == ".css" else REPO
    return (base / ref).resolve()


def _collect(source: Path, pattern: re.Pattern[str]) -> list[str]:
    text = source.read_text(encoding="utf-8")
    return [m.group(1) for m in pattern.finditer(text)]


def _frontend_sources() -> list[tuple[Path, re.Pattern[str]]]:
    pairs: list[tuple[Path, re.Pattern[str]]] = []
    for name in HTML_PAGES:
        pairs.append((REPO / name, HTML_REF))
    for css in sorted((REPO / "css").glob("*.css")):
        pairs.append((css, CSS_URL))
    for js in sorted((REPO / "js").glob("*.js")):
        pairs.append((js, JS_ASSET))
    return pairs


def _all_references() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    for source, pattern in _frontend_sources():
        if not source.exists():
            continue
        for ref in _collect(source, pattern):
            if _is_local(ref):
                out.append((source, ref))
    return out


def _wash_map(path: Path) -> dict[str, str]:
    return {k: v for k, v in WASH_ENTRY.findall(path.read_text(encoding="utf-8"))}


# ── ссылки ───────────────────────────────────────────────────────────────────
def test_every_referenced_asset_exists_on_disk():
    """Ловушка 7: PNG удалили/переименовали, а url() в CSS остался."""
    refs = _all_references()
    assert refs, "не нашли ни одной ссылки — сломался парсер, а не фронт"

    missing = [
        f"{source.relative_to(REPO)} → {ref}"
        for source, ref in refs
        if not _resolve(ref, source).exists()
    ]
    assert not missing, "ссылки в никуда:\n  " + "\n  ".join(sorted(missing))


def test_three_production_pages_are_covered():
    """Страховка на сам тест: если страницу переименуют, проверка не должна
    молча начать проверять пустоту."""
    for name in HTML_PAGES:
        assert (REPO / name).exists(), f"{name} пропала — обнови HTML_PAGES и CRITICAL-LINKS.md"


# ── кисти ────────────────────────────────────────────────────────────────────
def test_every_wash_brush_file_exists():
    """Ловушка 8: опечатка в имени кисти = прозрачная карточка слова."""
    wash = _wash_map(REPO / "js" / "words-data.js")
    assert len(wash) == 15, f"кистей должно быть 15, в карте {len(wash)} — новых не рисуем"

    missing = [f for f in wash.values() if not (REPO / "worte" / f).exists()]
    assert not missing, "кисти нет на диске:\n  " + "\n  ".join(sorted(missing))


def test_wash_map_has_no_second_copy_that_drifted():
    """`CLAUDE.md`: «js/words-data.js — единственный источник WASH».

    Копия в wb-card.js фактически существует (2026-07-26). Пока она есть, обе
    обязаны совпадать: разъехавшись, они дадут одному и тому же слову разные
    кисти в строке поиска и в карточке, и заметить это можно только глазом.
    """
    canonical = _wash_map(REPO / "js" / "words-data.js")
    card = _wash_map(REPO / "js" / "wb-card.js")
    if not card:
        pytest.skip("копии WASH в wb-card.js больше нет — инвариант восстановлен")

    assert card == canonical, (
        "две карты WASH разъехались. Канон — js/words-data.js.\n"
        f"  только в wb-card.js:   {sorted(set(card.items()) - set(canonical.items()))}\n"
        f"  только в words-data.js: {sorted(set(canonical.items()) - set(card.items()))}"
    )


def test_bare_filenames_in_js_resolve_to_a_real_asset():
    """Имя файла без папки, склеиваемое в рантайме.

    `js/schreiben.js` хранит листья roadmap как `'roadmap-leaf-1.png'` и лепит
    папку при отрисовке (`img.src = 'images/' + spot.img`). Грепом по «images/»
    такая ссылка не находится, и переименование файла ломает её молча — ровно
    как опечатка в WASH. Проверяем, что голое имя лежит хоть в одной из папок
    ассетов.
    """
    known = {p.name for d in ASSET_DIRS for p in (REPO / d).glob("*")}
    missing: list[str] = []
    for js in sorted((REPO / "js").glob("*.js")):
        for name in set(_collect(js, BARE_ASSET)):
            if name not in known:
                missing.append(f"{js.relative_to(REPO)} → {name}")
    assert not missing, (
        "имя файла есть в коде, файла нет в " + "/".join(ASSET_DIRS) + ":\n  "
        + "\n  ".join(sorted(missing))
    )


def test_no_orphan_brushes_in_worte():
    """Обратная сторона: файл в worte/ есть, а в карте его нет.

    Не ошибка сама по себе, но 15 кистей — закрытый набор, и лишний файл
    означает либо забытую правку карты, либо мусор в репозитории.
    """
    used = set(_wash_map(REPO / "js" / "words-data.js").values())
    on_disk = {p.name for p in (REPO / "worte").glob("*.png")}
    orphans = on_disk - used
    assert not orphans, f"кисти на диске, но не в WASH: {sorted(orphans)}"
