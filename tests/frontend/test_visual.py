"""Визуальные снапшоты трёх production-страниц.

Зачем. Весь класс багов, который в этом проекте ловился глазами и попадал в
`PLANS.md` пунктами 0f–0h, — пиксельный и молчаливый: мазок, растянутый строкой
до ~800 × 105; перевод в одну строку с многоточием поверх краски; карточка
744 px из списка против 440 px из поиска; левый рельс, срезанный на 34 px
авто-скроллом. Страница при этом не падает и в консоли чисто — сломанной её
делает только человеческий взгляд. Снимок ловит ровно это.

Как это работает. Первый прогон записывает эталон, дальше каждый прогон
сравнивает с ним попиксельно; при расхождении рядом с тестом появляются три
файла — эталон, факт и подсвеченный дифф.

Перезаписать эталоны осознанно:

    uv run pytest tests/frontend/test_visual.py --update-snapshots

⚠️ Эталоны привязаны к движку рендеринга. Записанные на macOS не совпадут с
Linux в CI — поэтому в CI эти тесты не гоняются: workflow отсекает их маркером
`-m "not visual"`. Это локальная сеть безопасности, не gate на merge.

⚠️ Отсекает именно маркер, а не фикстура. `live_site` пропускает тест, только
если успевает отработать первой, а поднимаются фикстуры в порядке сигнатуры —
поставь `page` раньше, и браузер дёрнется до пропуска. Там, где браузеров нет,
это ошибка, а не skip. Отсюда порядок `(live_site, page, assert_snapshot)`
во всех тестах ниже: он не косметический.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.visual


# Всё, что меняется само по себе между двумя прогонами: счётчики опроса,
# таймер Pomodoro, статусы сохранения. Не замаскируешь — тест будет падать
# каждый раз и его выключат через неделю.
PIPELINE_DYNAMIC = [
    "#elapsed", "#enrRate", "#enrFill", "#barFill", "#cardCount",
    "#enrKpis", "#enrFeed", "#enrStage", "#enrPhases", "#fleetStage",
    "#adminCard", "#cardResults", "#cardMore",
]
SCHREIBEN_DYNAMIC = [
    "#pomoTime", "#wordCount", "#saveStatus", "#anaStatus",
    "#essaysState", "#startState",
]


def _settle(page) -> None:
    """Дождаться, пока страница перестанет двигаться.

    `networkidle` мало: pipeline опрашивает API по таймеру и «idle» у него не
    наступает никогда. Поэтому ждём загрузку и даём фиксированную паузу на
    первый рендер, а живые числа гасим масками, а не ожиданием.
    """
    page.wait_for_load_state("load")
    page.wait_for_timeout(1200)


def test_woerterbuch_closed_state(live_site, page, assert_snapshot):
    """index.html — «Разворот» с закрытой карточкой: одна мера по центру."""
    page.goto(f"{live_site}/index.html")
    _settle(page)
    assert_snapshot(page, name="woerterbuch-closed.png", threshold=0.2)


def test_woerterbuch_open_card(live_site, page, assert_snapshot):
    """index.html — карточка открыта: тот самый разворот, в котором жил баг
    «карточка двух размеров» (744 px из списка против 440 px из поиска).

    ⚠️ Зависит от содержимого базы: снимок берётся по реальному ответу
    `/api/vocab/search`. Если база переобогатится и карточка `Wirkung`
    изменится — эталон надо перезаписать. Это осознанная цена: снимок пустой
    страницы не проверил бы ничего из того, ради чего тест написан.
    """
    page.goto(f"{live_site}/index.html")
    _settle(page)

    box = page.locator("input[type='search'], input[type='text']").first
    if box.count() == 0:
        pytest.skip("поле поиска не найдено — разметка index.html изменилась")
    box.fill("Wirkung")
    box.press("Enter")
    page.wait_for_timeout(1500)

    assert_snapshot(page, name="woerterbuch-open-card.png", threshold=0.2)


def test_schreiben_roadmap(live_site, page, assert_snapshot):
    """schreiben.html — roadmap, инструменты, фон, листья."""
    page.goto(f"{live_site}/schreiben.html")
    _settle(page)
    assert_snapshot(
        page, name="schreiben-roadmap.png", threshold=0.2,
        mask_elements=SCHREIBEN_DYNAMIC,
    )


def test_pipeline_dashboard(live_site, page, assert_snapshot):
    """pipeline.html — вёрстка панели. Живые числа замаскированы: проверяется
    раскладка, а не показания счётчиков."""
    page.goto(f"{live_site}/pipeline.html")
    _settle(page)
    assert_snapshot(
        page, name="pipeline-dashboard.png", threshold=0.2,
        mask_elements=PIPELINE_DYNAMIC,
    )


def test_header_on_mobile_width(live_site, page, assert_snapshot):
    """Единая шапка на мобильной ширине — двухстрочный вариант с собственным
    фоном (`header-wash-mobile.png`). Ломается независимо от десктопной."""
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{live_site}/index.html")
    _settle(page)
    assert_snapshot(page, name="header-mobile.png", threshold=0.2)
