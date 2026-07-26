"""Общие фикстуры для фронтовых тестов.

Визуальные тесты стреляют по ЖИВОМУ стеку (`make up`, nginx :8753), а не по
файлам: половина верстки зависит от данных из API, и снимок статики ничего бы
не доказал. Поэтому единственный честный режим — «стек поднят или пропускаем».

Пропуск, а не падение, потому что `make test` обязан оставаться зелёным на
машине без докера и в CI, где стека нет вовсе.
"""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

SITE = "http://localhost:8753"

# Ширина, на которой сделаны все замеры вёрстки в PLANS.md («на 1440 px…»).
# Меняя её, вы обесцениваете эталоны — их придётся перезаписать все разом.
VIEWPORT = {"width": 1440, "height": 900}


def _site_is_up(timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(f"{SITE}/", timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError):
        return False


@pytest.fixture(scope="session")
def live_site() -> str:
    if not _site_is_up():
        pytest.skip(f"{SITE} не отвечает — подними стек (`make up`), иначе снимать нечего")
    return SITE


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):  # noqa: F811 — переопределяем фикстуру плагина
    return {
        **browser_context_args,
        "viewport": VIEWPORT,
        "device_scale_factor": 1,
        # Гасит анимации: листья roadmap и «муравьи» коннектора иначе попадают
        # в кадр в случайной фазе, и каждый прогон отличается от эталона.
        "reduced_motion": "reduce",
        "locale": "ru-RU",
        "timezone_id": "Europe/Berlin",
    }
