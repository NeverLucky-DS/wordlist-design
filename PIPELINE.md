# Word Enrichment Pipeline — Deutsch Essay Wörterbuch

> Автономный пайплайн: тема → источники → слова → обогащение → БД.  
> Вход — название темы + опциональный список статей. Выход — пополненная БД с отчётом об ошибках.

---

## v2 (июнь 2026) — что изменилось

Проблемы v1: разброс выхода 5–52 слова на тему, ~45% слов терялось на точном
Wiktionary-поиске, грязные строки в БД («die Anpassung (an + Akk.)»), клише не
собирались вообще, запуск только ручной.

| Изменение | Файл | Эффект |
|---|---|---|
| Нормализация: чистка + лемматизация (simplemma), в БД пишется лемма без артикля | `pipeline/normalize.py` | Wiktionary-потери ↓, нет грязных записей/дублей |
| Батч-обогащение: N слов за 1 вызов Mistral (`pipeline_batch_size`, дефолт 6) | `pipeline/enrichment.py` | 50 слов ≈ 7 вызовов вместо 50 → нет 429 |
| Слова из статей без словарной статьи больше не выбрасываются (Mistral заполняет грамматику сам); сгенерированные — обязаны найтись в Wiktionary/DWDS | `pipeline/enrichment.py` | Полнота ↑, галлюцинации в БД не попадают |
| Control loop: добор до `pipeline_target_words` (дефолт 45) прямой генерацией + верификацией, до 2 раундов | `pipeline/runner.py`, `pipeline/supplement.py` | Стабильно 40–50 слов на тему |
| Redemittel: извлечение из статей (в том же вызове, что и слова) + добор до `pipeline_min_phrases` (12) по частям эссе | `pipeline/extraction.py`, `supplement.py` | Точные клише с `essay_part`/уровнем |
| Упавшие слова → `word_failures`, авто-ретрай в следующем прогоне (до 3 попыток) | `pipeline/runner.py` | Самовосстановление |
| Очередь тем + фоновый планировщик в FastAPI (`pipeline_interval_minutes`, недобравшие темы перезапускаются) | `pipeline/scheduler.py`, `POST /api/pipeline/queue` | Работает само по себе |
| Чистка наследия v1 при старте приложения (леммы, дубли) | `main.py`, `topic_pack_service.py` | Идемпотентно |

Автономный режим: `POST /api/pipeline/queue {"topics": ["Migration", ...], "target_words": 45}` —
дальше бэкенд сам обработает очередь и доберёт темы до цели. Настройки — env-переменные
`PIPELINE_*` (см. `app/config.py`).

---

## v3 — полная автономность и большие наборы слов

| Изменение | Файл | Эффект |
|---|---|---|
| Общий Mistral-хелпер: Retry-After, межпоточный cooldown, единый ретрай | `pipeline/mistral_http.py` | Один источник правды для 429-логики; параллельные воркеры не добивают залимиченный API |
| Crash-recovery: зависшие queue-items → pending, протухшие runs (>`pipeline_stale_run_minutes`) → failed | `pipeline/scheduler.py` | Очередь не встаёт колом после рестарта/падения |
| Автотемы: пустая очередь автоматически пополняется из каталога ~30 экзаменационных тем (TestDaF/Goethe/DSH), затем LLM-генерация новых | `pipeline/topics_catalog.py` | База растёт сама, без ручного ввода тем |
| Maintenance-requeue: done-темы ниже цели возвращаются в очередь (до `pipeline_max_attempts`) | `pipeline/scheduler.py` | Недобравшие темы догоняются со временем |
| target 45→60, раунды добора 2→3 с фокусом: общий → глаголы+рекция → прилагательные+композиты | `config.py`, `supplement.py` | Большие сбалансированные наборы, а не 60 существительных |
| `GET /api/pipeline/overview` — слова/фразы/ошибки по темам, очередь, настройки одним вызовом; `GET /api/pipeline/failures` | `api/routes/pipeline.py` | Готовый бэкенд для дашборда |
| Нормализация регистра тем (Klimawandel → klimawandel) в стартовой чистке | `topic_pack_service.py` | Темы не раздваиваются |

Цикл планировщика: recover_stale → maintenance_requeue → ensure_topics (автотемы) →
process_next_topic. Достаточно поднять бэкенд с `MISTRAL_API_KEY` — дальше система
сама наполняет базу: ~60 слов + ~12 клише на тему, темы из каталога, ошибки
ретраятся, зависания лечатся.

---

## 1. Структура данных слова (целевая схема БД)

```sql
-- Базовая таблица слов
CREATE TABLE words (
    id          SERIAL PRIMARY KEY,
    de          TEXT NOT NULL UNIQUE,   -- "analysieren", "der Abstand"
    article     TEXT,                   -- 'Der' | 'Die' | 'Das' | NULL (verbs/adj)
    pos         TEXT NOT NULL,          -- 'Noun' | 'Verb' | 'Adjective' | 'Other'
    level       TEXT,                   -- 'B1' | 'B2' | 'C1'
    ru          TEXT,                   -- основной перевод
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Грамматика (Rektion / Verwendung / управление)
CREATE TABLE grammar_data (
    word_id     INT REFERENCES words(id),
    rektion     TEXT,           -- 'an + Dat.', 'über + Akk.' и т.д.
    ready_phrase TEXT,          -- готовая фраза: "auf etwas (Akk.) hinweisen"
    declension  JSONB,          -- таблица склонения / спряжения
    extra       JSONB           -- доп. поля (Komparativ, Partizip II и т.д.)
);

-- Примеры употребления
CREATE TABLE examples (
    id          SERIAL PRIMARY KEY,
    word_id     INT REFERENCES words(id),
    text_de     TEXT NOT NULL,
    text_ru     TEXT,
    source_url  TEXT,           -- откуда взят пример
    is_ai       BOOLEAN DEFAULT false  -- сгенерирован LLM или из источника
);

-- Темы
CREATE TABLE topics (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE   -- 'Klimawandel', 'Migration' и т.д.
);

-- Связь слово↔тема (M:N)
CREATE TABLE word_topics (
    word_id   INT REFERENCES words(id),
    topic_id  INT REFERENCES topics(id),
    PRIMARY KEY (word_id, topic_id)
);
```

---

## 2. Откуда берётся каждое поле

| Поле | Источник | Метод |
|---|---|---|
| `de`, `article`, `pos` | Wiktionary API | парсинг без LLM |
| `level` | CEFR-разметка Wiktionary / OpenDict | парсинг |
| `ru` | Wiktionary `de` → `ru` секция | парсинг |
| `rektion`, `ready_phrase` | Wiktionary «Bedeutungen» + «Rektion» | парсинг → Mistral |
| `declension` (JSONB) | Wiktionary таблицы склонения | парсинг → Mistral |
| `examples[0..2]` | Исходные статьи (шаг 2) | LLM-экстракция |
| `examples[доп.]` | Mistral — дополняет до 3 | LLM-генерация |
| `topic` | задаётся вручную при создании темы | — |

---

## 3. Пайплайн (высокий уровень)

```
[Пользователь вводит тему]
         │
         ▼
   ┌─────────────┐
   │  Step 1     │  Grok API — поиск качественных источников
   │  Source     │  (эссе, статьи, академические тексты по теме)
   │  Discovery  │  → stack: List[str]  (URL-ки)
   └──────┬──────┘
          │ async (все URL параллельно)
          ▼
   ┌─────────────┐
   │  Step 2     │  Парсинг статей + LLM-экстракция слов
   │  Article    │  httpx + BeautifulSoup → текст
   │  Parsing    │  Mistral: найди топ-30 essay-слов + 1-3 примера каждого
   └──────┬──────┘
          │ merge + dedup
          ▼
   ┌─────────────┐
   │  Step 3     │  Роутинг слов
   │  Word       │  слово есть в БД → только добавить topic
   │  Router     │  слова нет → запуск Step 4
   └──────┬──────┘
          │ async (все новые слова параллельно)
          ▼
   ┌─────────────┐
   │  Step 4     │  Обогащение слова
   │  Word       │  Wiktionary API → сырые данные
   │  Enrichment │  Mistral → структурированный JSON
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  Step 5     │  Запись в PostgreSQL
   │  DB Write   │  upsert + связь с темой
   └──────┬──────┘
          │
          ▼
   [Отчёт об ошибках → пользователю]
```

---

## 4. Детальное описание шагов

### Step 1 — Source Discovery (Grok API)

```python
# Промпт для Grok
PROMPT = """
Найди 8-12 качественных немецкоязычных источников (эссе, журнальные статьи, академические тексты)
по теме: "{topic}".
Критерии: уровень языка B2–C2, богатая лексика, эссе-стиль (аргументация, выводы).
Верни JSON: [{{"url": "...", "title": "...", "type": "essay|article|academic"}}]
"""
```

**Выход:** `List[SourceItem]` — стек URL-ов на обработку.

---

### Step 2 — Article Parsing + Word Extraction

Два подшага для каждого URL (параллельно через `asyncio.gather`):

**2a. Парсинг (без LLM):**
```python
async def fetch_article(url: str) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=15)
    soup = BeautifulSoup(r.text, "lxml")
    # убрать nav/footer/scripts, взять основной текст
    return soup.get_text(separator=" ", strip=True)
```

**2b. Экстракция слов (Mistral):**
```python
EXTRACTION_PROMPT = """
Текст статьи на немецком ниже. Задача:
1. Найди 15-25 слов/фраз уровня B2-C1, характерных для эссе на тему "{topic}".
2. Для каждого — 1-3 примера ТОЧНО из этого текста (предложения с этим словом).
3. Пометь часть речи и артикль (для существительных).

Формат ответа — строго JSON:
[{{"word": "der Klimawandel", "pos": "Noun", "examples": ["...", "..."]}}]

Текст:
{text}
"""
```

**Выход:** `List[WordCandidate]` — слова + примеры из статьи.

---

### Step 3 — Word Router

```python
async def route_words(candidates: List[WordCandidate], topic_id: int, db: AsyncSession):
    for candidate in candidates:
        existing = await db.scalar(
            select(Word).where(Word.de == candidate.word)
        )
        if existing:
            # просто привязываем тему
            await db.execute(insert(WordTopic).values(
                word_id=existing.id, topic_id=topic_id
            ).on_conflict_do_nothing())
        else:
            # кладём в очередь обогащения
            enrichment_queue.put_nowait(candidate)
```

---

### Step 4 — Word Enrichment

**4a. Wiktionary API (парсинг):**

```
GET https://de.wiktionary.org/w/api.php
  ?action=parse
  &page={word}
  &prop=wikitext|sections
  &format=json
```

Из викитекста извлекаем:
- `{{Wortart}}` → POS
- `{{Deutsch Substantiv Übersicht}}` → таблица склонения
- `{{Deutsch Verb Übersicht}}` → таблица спряжения  
- `{{Bedeutungen}}` → определения + Rektion
- `{{Übersetzungen}}` → русский перевод
- `{{Referenzen}}` → уровень (иногда есть)

**4b. Mistral — структурирование:**

```python
STRUCTURE_PROMPT = """
Ниже сырые данные из Wiktionary для немецкого слова "{word}".
Верни строго JSON по схеме:
{{
  "article": "Der|Die|Das|null",
  "pos": "Noun|Verb|Adjective|Other",
  "level": "B1|B2|C1|null",
  "ru": "основной перевод на русский",
  "rektion": "управление, напр. 'auf + Akk.'",
  "ready_phrase": "готовая фраза с управлением",
  "declension": {{...таблица или спряжение...}},
  "examples_needed": 0|1|2  // сколько примеров дополнить (до 3 итого)
}}

Если examples_needed > 0 — добавь их в поле "examples_generated": ["..."].

Сырые данные:
{wikitext}
"""
```

---

### Step 5 — DB Write

```python
async def write_word(data: EnrichedWord, topic_id: int, candidates_examples: List[str], db: AsyncSession):
    word = Word(**data.base_fields)
    db.add(word)
    await db.flush()  # получаем id

    db.add(GrammarData(word_id=word.id, **data.grammar_fields))

    all_examples = candidates_examples + data.examples_generated
    for ex in all_examples[:3]:
        db.add(Example(word_id=word.id, text_de=ex, is_ai=ex in data.examples_generated))

    db.add(WordTopic(word_id=word.id, topic_id=topic_id))
    await db.commit()
```

---

## 5. Конкурентность и архитектура

### Стратегия параллелизма

```
Шаг 1 (Grok)       — 1 запрос, sequential
Шаг 2 (парсинг)    — asyncio.gather(*[fetch_article(url) for url in sources])
Шаг 2 (экстракция) — asyncio.gather(*[extract_words(text) for text in articles])
Шаг 4 (Wiktionary) — asyncio.Semaphore(5) — не более 5 параллельных запросов (rate limit)
Шаг 4 (Mistral)    — asyncio.Semaphore(3) — лимит на токены/мин
```

### Очередь слов

```python
import asyncio

enrichment_queue: asyncio.Queue[WordCandidate] = asyncio.Queue()

async def enrichment_worker(worker_id: int, db_pool):
    while True:
        candidate = await enrichment_queue.get()
        try:
            wikitext = await fetch_wiktionary(candidate.word)
            structured = await call_mistral(wikitext, candidate)
            async with db_pool.acquire() as db:
                await write_word(structured, ...)
        except Exception as e:
            error_log.append({"word": candidate.word, "error": str(e), "worker": worker_id})
        finally:
            enrichment_queue.task_done()

# Запускаем N воркеров
workers = [asyncio.create_task(enrichment_worker(i, db_pool)) for i in range(5)]
```

### Технологический стек

| Слой | Технология | Зачем |
|---|---|---|
| HTTP-клиент | `httpx` (async) | парсинг статей + Wiktionary API |
| Парсинг HTML | `BeautifulSoup4` + `lxml` | извлечение текста статей |
| LLM-вызовы | `mistralai` SDK (async) | структурирование + дополнение |
| Поиск источников | Grok API (`x.ai`) | discovery |
| БД | `asyncpg` + `SQLAlchemy 2.0` async | хранение |
| API-слой | `FastAPI` | endpoint `/topic` (POST) |
| Очереди | `asyncio.Queue` | воркер-пул обогащения |
| Конфигурация | `pydantic-settings` | env vars |

---

## 6. FastAPI endpoint (точка входа для пользователя)

```python
@router.post("/topic")
async def process_topic(
    name: str,
    article_urls: list[str] = [],   # опционально, через запятую
    background_tasks: BackgroundTasks = ...,
    db: AsyncSession = Depends(get_db),
):
    topic = await get_or_create_topic(name, db)
    background_tasks.add_task(run_pipeline, topic.id, name, article_urls)
    return {"status": "started", "topic_id": topic.id}

@router.get("/topic/{topic_id}/report")
async def get_report(topic_id: int, db: AsyncSession = Depends(get_db)):
    # возвращает прогресс + список ошибок
    ...
```

Пользователь делает POST → сразу получает `topic_id` → пайплайн работает в фоне → через GET `/report` можно проверить статус и ошибки.

---

## 7. Обработка ошибок и отчёт

```python
@dataclass
class PipelineError:
    stage: Literal["fetch", "extract", "wiktionary", "mistral", "db"]
    item: str          # URL или слово
    error: str
    timestamp: datetime

# В конце пайплайна:
async def send_report(topic_id: int, errors: list[PipelineError]):
    report = {
        "topic_id": topic_id,
        "words_added": ...,
        "words_linked": ...,
        "errors": [asdict(e) for e in errors],
    }
    # сохраняем в БД / логируем / отправляем уведомление
```

Типы ошибок и стратегия retry:

| Ошибка | Retry | Поведение |
|---|---|---|
| HTTP 429 (rate limit) | 3× с exponential backoff | ждём и повторяем |
| HTTP 404 (слово не найдено в Wiktionary) | — | логируем, слово пропускаем |
| Mistral timeout | 2× | повторяем |
| Mistral невалидный JSON | 1× с уточняющим промптом | fallback → partial save |
| DB unique violation | — | on_conflict_do_nothing |

---

## 8. Что это даёт для Сбер-стажировки

Проект **напрямую покрывает требования вакансии**:

| Требование | Реализация в проекте |
|---|---|
| **Async Python** | `asyncio.gather`, `asyncio.Queue`, `httpx` async, `asyncpg` |
| **FastAPI + REST API** | endpoint `/topic` (POST) + `/report` (GET) |
| **PostgreSQL** | схема выше, `SQLAlchemy 2.0 async` |
| **Агентные решения** | двухагентная схема: Grok (discovery) + Mistral (structuring) |
| **Тесты** | unit: mock Wiktionary API; integration: test DB + real Mistral |
| **Git** | feature-branches per pipeline stage |

Плюс к этому — **паттерн, который используют в Сбере**: оркестратор (FastAPI endpoint) → планировщик (роутер слов) → исполнители (воркеры обогащения) → валидатор (Mistral JSON schema). Это буквально ReAct-топология через граф воркеров.

---

## 9. Порядок реализации (рекомендуемый)

1. `db/models.py` — SQLAlchemy модели по схеме выше
2. `services/wiktionary.py` — парсер Wiktionary API (без LLM, тесты дешёвые)
3. `services/mistral.py` — async-обёртка над Mistral SDK
4. `pipeline/enrichment.py` — воркер + очередь (Step 4)
5. `pipeline/extraction.py` — парсинг статей + экстракция слов (Step 2)
6. `pipeline/discovery.py` — Grok API (Step 1)
7. `api/routes.py` — FastAPI endpoints
8. `tests/` — unit + integration тесты
