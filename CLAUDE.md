# CLAUDE.md

Deutsch Essay Trainer — B1–C1 немецкий: тематический словарь, essay roadmap (Schreiben), pipeline обогащения слов по теме.

## Начни отсюда (карта проекта)

@info/README.md
@info/CRITICAL-LINKS.md

## Стек

FastAPI + PostgreSQL (`backend/`) · vanilla HTML/JS/CSS без сборки (фронт) · nginx · Docker Compose · pytest (36 тестов)

## Команды

- Запуск: `docker compose up --build`
- Тесты: `cd backend && pytest -v` — прогонять после любых правок в `backend/`, не считать backend-задачу готовой, если тесты не зелёные
- Граф проекта: `graphify-out/GRAPH_REPORT.md` — свежесть проверяется через `git rev-parse HEAD` vs commit в отчёте; после крупных структурных правок запусти `graphify update .`

## Опасные места (сверяться, а не гадать)

- `js/words-data.js` — единственный источник `WASH`/`brushOf`/`PIPELINE_WASHES`, используется в `index.html`, `schreiben.html`, `pipeline.html`. Не дублировать данные по страницам — правь только здесь.
- Pipeline: `backend/app/pipeline/runner.py` — канонический путь обогащения слов (v2, в проде). `content_llm.py` / `verify.py` — экспериментальный/устаревший путь (v3, см. `info/known-debt.md`). Не путать при правках enrichment-логики.
- `backend/data/*.db`, `backend/scripts/*`, `backend/audit_db.py` — локальные БД и ручные maintenance-CLI, не трогать и не запускать автоматически без явной просьбы.
- Перед удалением или переименованием любого файла — сверься с `info/CRITICAL-LINKS.md` (карта зависимостей).
