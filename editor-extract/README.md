# Essay Editor — полный модуль

Полностью изолированный модуль редактора немецких эссе с ИИ-анализом (Mistral).
Содержит всё: бэкенд (FastAPI), фронтенд (React + TipTap), схемы, модели, сервисы и стили.

---

## Структура папки

```
editor-extract/
├── README.md                        ← этот файл
│
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  ← FastAPI + CORS
│       ├── config.py                ← переменные окружения (.env)
│       ├── schemas.py               ← Pydantic-схемы (Essay, EssayAnalysis, Word, Phrase…)
│       ├── db/
│       │   ├── models.py            ← SQLAlchemy ORM (Essay, EssayAnalysis, Word, Phrase…)
│       │   └── session.py           ← async engine + get_db()
│       ├── api/routes/
│       │   ├── essays.py            ← /api/essays, включая /analyze/stream
│       │   ├── words.py             ← /api/words
│       │   ├── phrases.py           ← /api/phrases
│       │   ├── topics.py            ← /api/topics
│       │   └── health.py            ← /health
│       └── services/
│           ├── essays_repo.py       ← CRUD эссе + save_analysis
│           ├── mistral_analyzer.py  ← ВСЯ логика ИИ-анализа (см. ниже)
│           ├── words_repo.py        ← запросы слов
│           ├── phrases_repo.py      ← запросы клише
│           ├── topic_pack_service.py← загрузка .topic.yaml → БД
│           ├── wiktionary_client.py ← Wiktionary fetch
│           ├── grammar_parser.py    ← normalize_wiktionary_entry → grammar_data
│           └── user_stats_service.py← запись активности (streak)
│
└── frontend/
    └── src/
        ├── api.ts                   ← типизированный HTTP-клиент
        ├── editor/
        │   ├── EditorShell.tsx      ← главный компонент, оркестрирует всё
        │   ├── ManuscriptColumn.tsx ← центральная колонка (редактор + слово-карточка)
        │   ├── SectionEditor.tsx    ← обёртка TipTap EditorContent
        │   ├── ManuscriptSectionTabs.tsx ← табы секций
        │   ├── AnnotationPopover.tsx     ← попап при клике на ошибку
        │   ├── EditorialNotePanel.tsx    ← боковая панель заметок
        │   ├── MaterialsDesk.tsx    ← правая панель (клише, слова, кнопка Анализ)
        │   ├── TopicVocabBlock.tsx  ← блок слов темы в MaterialsDesk
        │   ├── TopicWordDetail.tsx  ← детали слова в MaterialsDesk
        │   ├── EssayMap.tsx         ← левая навигация по блокам
        │   ├── EditorStatusBar.tsx  ← строка статуса внизу
        │   ├── EditorHeaderChrome.tsx ← шапка редактора
        │   ├── LevelBadge.tsx       ← бейдж уровня (B1/B2/C1)
        │   ├── LineGutter.tsx       ← номера строк слева от редактора
        │   ├── NewEssayButton.tsx   ← кнопка «Новое эссе»
        │   ├── KlischeeCard.tsx     ← карточка клише
        │   ├── PomodoroTimer.tsx    ← таймер помодоро
        │   ├── editorMetaContext.tsx ← React Context (level + setter)
        │   ├── editorDraft.ts       ← localStorage черновик
        │   ├── essayText.ts         ← buildEssayText / parseEssayText
        │   ├── topicVocab.ts        ← утилиты темы
        │   ├── wordFocus.ts         ← управление фокусом слова
        │   ├── errorUtils.ts        ← mapErrorsToBlocks, reanchor, buildErrorId…
        │   ├── constants.ts         ← BLOCKS, DEFAULT_PHRASES, STAGE_HELPERS…
        │   ├── types.ts             ← BlockKey, SelectedError, ErrorAnchor
        │   ├── useLiveAnchorRect.ts ← rect аннотации для позиционирования попапа
        │   ├── editorial.css        ← все стили редактора (Wörterbuch-дизайн)
        │   └── tiptap/
        │       ├── useSectionEditor.ts  ← useEditor + refreshMarks
        │       └── annotationMark.ts    ← TipTap Mark (span[data-annotation])
        └── dictionary/
            ├── WordDetailCard.tsx   ← карточка слова (всплывает в редакторе)
            ├── WordWashRow.tsx      ← строка слова с акварелью
            ├── brushAssets.ts       ← пути к webp-кистям + posLabel + levelColors
            ├── wordDisplay.ts       ← splitGermanLemma, formatGermanHeadline
            ├── wordGrammar.ts       ← buildWordCardModel (grammar_data → view model)
            ├── useWordTremble.ts    ← hover микро-дрожание
            └── dictionary.css       ← стили словарных компонентов (используются в редакторе)
```

---

## Как работает редактор — от кнопки «Анализировать» до подсветки

### 1. Структура эссе

Эссе разбито на **4 блока** (`BlockKey`):

| Ключ | Название | Роль |
|---|---|---|
| `einleitung` | Einleitung | Введение, тезис |
| `argument1` | Argument Eins | Первый аргумент |
| `argument2` | Argument Zwei | Второй аргумент |
| `schluss` | Schluss | Заключение |

Каждый блок — отдельный `<SectionEditor>` (TipTap), вся конкатенация хранится в `blocks: Record<BlockKey, string>` в `EditorShell`.

---

### 2. Сохранение эссе

**Автосохранение** — 2 секунды после последнего изменения (`scheduleAutosave`):
```
onBlockChange → scheduleAutosave(nextBlocks)
  → setTimeout(2000) → buildEssayText(blocks)
  → saveEssay(text, silent=true)
  → POST /api/essays  (первый раз)
  → PATCH /api/essays/{id}  (последующие)
```

Дополнительно: `visibilitychange` / `beforeunload` → `flushSave()` (немедленная запись).

`buildEssayText(blocks)` в `essayText.ts` собирает текст эссе в формате:
```
Einleitung:
<текст блока>

Argument Eins:
<текст блока>
...
```
и возвращает `{ text, ranges }` — `ranges` это `{ [blockKey]: { start, end } }` —
офсеты каждого блока в общей строке (нужны для маппинга ошибок).

---

### 3. Запуск анализа → SSE-стрим

```
[Кнопка Analysieren]
  → EditorShell.handleAnalyze()
    → saveEssay(text)         ← сохраняет актуальный текст
    → analyzeEssayStream(id, onEvent)   [api.ts]
      → POST /api/essays/{id}/analyze/stream
        → FastAPI StreamingResponse
          → iter_analyze_events(text, essay_type, level)
            │
            ├── для каждого блока: yield { type:"part_start", part, label }
            ├──   Mistral API → JSON ответ
            ├──   yield { type:"part_done", errors[], all_errors[], part_reports[] }
            └── финальный запрос: yield { type:"done", overall_score, grade, ... }
```

На клиенте `analyzeEssayStream` читает `ReadableStream` через `reader.read()`,
разбивает буфер по `\n\n`, парсит `data: {...}` строки, вызывает колбэк `onEvent`.

**Три типа событий:**

| type | Когда | Что делает фронтенд |
|---|---|---|
| `part_start` | перед запросом к Mistral | `setAnalyzeProgress("Analysiere Einleitung…")` |
| `part_done` | после ответа на блок | `applyPartialAnalysis()` — сразу показывает ошибки этого блока |
| `done` | всё готово | `applyAnalysis()` — финальные оценка, grade, summary |

---

### 4. Как работает Mistral-анализ (`mistral_analyzer.py`)

#### Шаг A — Разбивка текста на части

`_extract_parts(text)` ищет маркеры `"Einleitung:\n"`, `"Argument Eins:\n"` и т.д.
Возвращает `dict[part_key → text]`.

#### Шаг B — Промпт на каждый блок (`_build_part_prompt`)

Промпт на русском, отправляется в Mistral как `user` сообщение.
Содержит:
- роль («строгий и доброжелательный преподаватель»)
- название части, тип эссе, уровень (B1/B2/C1)
- инструкции по категориям ошибок: `grammar|style|weak|vocabulary`
- инструкции по серьёзности: `critical|medium|suggestion`
- инструкции по `annotation_kind`: `critical|style|b2_potential|good_fragment|suggestion`
- формат ответа: `{ part_score, part_feedback_ru, errors[] }`
- уже выданные замечания (`previous_points`) → чтобы не повторяться

Структура каждой ошибки в ответе Mistral:
```json
{
  "start": 14,
  "end": 28,
  "excerpt": "heutzutage ist",
  "type": "grammar",
  "severity": "critical",
  "annotation_kind": "critical",
  "explanation_ru": "Что не так: ...\nПочему: ...\nКак исправить: ...",
  "correction": "Heutzutage ist",
  "rule": "Заглавная буква в начале предложения",
  "what_wrong_ru": "Строчная буква в начале",
  "why_bad_ru": "В немецком предложения всегда начинаются с заглавной буквы",
  "how_to_fix_ru": "1) Заглавная буква. 2) Проверьте остальные предложения.",
  "b1_variant_de": "Heutzutage ist ...",
  "b2_variant_de": "In der heutigen Zeit ...",
  "b1_explain_ru": "Простой вариант",
  "b2_explain_ru": "Более академично",
  "study_phrases_de": ["Heutzutage ...", "In der heutigen Zeit ..."]
}
```

API-запрос:
```python
POST https://api.mistral.ai/v1/chat/completions
{
  "model": "mistral-large-latest",
  "messages": [
    { "role": "system", "content": "Return only valid JSON. No markdown." },
    { "role": "user",   "content": "<промпт>" }
  ],
  "temperature": 0.2,
  "response_format": { "type": "json_object" }
}
```

#### Шаг C — Нормализация и дедупликация

`_normalize_error_ranges(errors, text, part_key)`:
- Ищет `excerpt` в тексте блока (ближайший к `start`, если несколько совпадений)
- Клипует `start/end` к реальной длине текста
- Инфeрит `annotation_kind` если Mistral не вернул его

`_dedupe_errors_part(errors)` — убирает дубликаты по `excerpt+start+end`.

`_error_has_anchor(err, part_text)` — проверяет, что ошибка действительно привязана к тексту (для отсева «фантомных» ошибок).

#### Шаг D — Финальный запрос (`_build_final_prompt`)

После всех блоков — отдельный вызов Mistral:
```json
{
  "structure_feedback_ru": "...",
  "topic_feedback_ru": "...",
  "strengths_ru": ["..."],
  "next_steps_ru": ["..."],
  "overall_comment_ru": "..."
}
```

#### Шаг E — Оценка

```python
overall_score = avg(part_scores)   # только непустые блоки
grade = "A" если >=85, "B" >=70, "C" >=55, иначе "D"
```

Итог `yield { type:"done", overall_score, grade, errors, part_reports, final_summary, model }`.

#### Фолбэк (нет MISTRAL_API_KEY)

`_fallback_analysis(parts)` — генерирует предустановленный ответ с одной `suggestion`-ошибкой на блок. Редактор работает без ключа.

---

### 5. Маппинг ошибок на блоки (`errorUtils.ts`)

Mistral возвращает ошибки с `part: "einleitung"` и `start/end` внутри блока.
Если `part` не распознан — используется `ranges` из `buildEssayText` для определения блока по глобальному офсету.

```
mapErrorsToBlocks(errors, blocks, ranges)
  → для каждой ошибки: определить owner (по err.part или по ranges)
  → normalizeErrorForBlock(err, blockText)
      → findExcerptIndex(blockText, excerpt, hintStart)  ← ищет excerpt в тексте
      → клипует start/end
  → buildErrorId(part, err)  ← стабильный хеш для data-error-id
  → mergeOverlappingErrors()  ← объединяет ошибки с одинаковым excerpt
```

После каждого изменения текста — `reanchorAllBlocks(blocks, errorsByBlock)`:
пересчитывает позиции существующих ошибок по excerpt. Ошибки, которые больше не найдены, помечаются `orphaned: true` (не отображаются, но сохраняются).

---

### 6. Отображение аннотаций в TipTap

`useSectionEditor.ts` → `refreshMarks(editor, errors)`:

1. Удаляет все старые `annotation` марки через `tr.removeMark`
2. Перебирает активные (не `orphaned`) ошибки, от конца к началу (чтобы не сдвигать позиции)
3. Устанавливает `setTextSelection({ from: 1+start, to: 1+end })`
4. Применяет `setMark("annotation", { kind, errorId })`

`AnnotationMark` (`annotationMark.ts`) рендерит:
```html
<span data-annotation="critical" data-error-id="e1a2b3">текст ошибки</span>
```

CSS в `editorial.css` / `dictionary.css` подсвечивает по `data-annotation`:

| `annotation_kind` | Цвет подчёркивания |
|---|---|
| `critical` | красный |
| `style` | оранжевый |
| `b2_potential` | синий |
| `good_fragment` | зелёный |
| `suggestion` | серый пунктир |

---

### 7. Попап аннотации (`AnnotationPopover.tsx`)

При клике на `<span data-error-id>`:
```
handleClick в TipTap editorProps
  → ищет err по error_id в errorsRef
  → onErrorClick(err, errorId)
    → EditorShell: setSelectedError + setErrorAnchor
    → useLiveAnchorRect(errorAnchor)
        → querySelector(`[data-error-id="${errorAnchor.errorId}"]`)
        → getBoundingClientRect() + requestAnimationFrame
    → <AnnotationPopover error={...} anchorRect={rect} />
```

Попап показывает:
- `explanation_ru` — 3-строчное объяснение (Что не так / Почему / Как исправить)
- `correction`, `b1_variant_de`, `b2_variant_de`
- `study_phrases_de` — фразы для словаря
- кнопки «Вставить» и «В тренировку»

---

### 8. Правая панель — `MaterialsDesk`

- `TopicVocabBlock` → список слов темы из `/api/words?topic=...`
- `KlischeeCard` → клише из `/api/phrases?part=...&topic=...`
- кнопка **Analysieren** → `onAnalyze` → `handleAnalyze()` в `EditorShell`
- `PomodoroTimer` — автономный таймер
- при клике на слово → `selectSidebarWord` → `fetchWord(id)` → `setFloatWord`
  → `WordDetailCard` всплывает в `ManuscriptColumn`

---

### 9. Словарные компоненты (`dictionary/`)

Используются **только** внутри редактора, не для страницы Wörterbuch.

| Файл | Роль |
|---|---|
| `WordDetailCard.tsx` | Карточка слова с грамматикой, склонением, примерами |
| `WordWashRow.tsx` | Строка слова с акварельным фоном-кистью |
| `brushAssets.ts` | `getBrushUrl(level, wordType)` → `/assets/wordlist/brushes/…webp` |
| `wordDisplay.ts` | `formatGermanHeadline(word)` → `"der Baum"` / `"laufen"` |
| `wordGrammar.ts` | `buildWordCardModel(word)` → секции грамматики для рендера |
| `useWordTremble.ts` | hover-микроанимация на немецком слове |
| `dictionary.css` | `.dict-*`, `.word-wash-*` стили |

---

### 10. Хранение черновика (`editorDraft.ts`)

`localStorage` ключ `editor_draft`:
```ts
{ essayId: number | null, blocks: Record<BlockKey, string>, essayMeta: {...} }
```
При открытии `/editor` без ID → `loadEditorDraft()` → redirect на `/editor/{id}`.
При каждом изменении → `saveEditorDraft(...)`.
`clearEditorDraft()` — при «Новое эссе».

---

### 11. БД модели (только для редактора)

| Таблица | Поля | Роль |
|---|---|---|
| `essays` | id, title, text, essay_type, topic, level, created_at, updated_at | Эссе |
| `essay_analyses` | id, essay_id, errors_json (JSONB), overall_score, grade, text_snapshot, part_reports_json (JSONB), final_summary_json (JSONB), model, created_at | Результаты анализа |
| `words` | id, german, article, word_type, translation_ru, level, grammar_data (JSONB), examples (JSONB) | Словарные слова |
| `word_topics` | id, word_id, topic | Привязка слова к теме |
| `phrases` | id, text_de, translation_ru, essay_part, topic, level | Клише-фразы |
| `user_phrase_known` | id, user_id, phrase_id, known | Отметка «знаю» |
| `user_stats` | id, user_id, streak_current, streak_last_date, total_words_learned | Статистика |

`errors_json` хранится как `{ "errors": [...] }`.
`part_reports_json` хранится как `{ "items": [...] }`.

---

## Установка и запуск

### Backend

```bash
cd editor-extract/backend

# .env (создать рядом с app/)
MISTRAL_API_KEY=your_key_here
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
CORS_ORIGINS=http://localhost:5173

pip install -r requirements.txt
alembic upgrade head          # применить миграции (скопировать из оригинала)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
# Зависимости TipTap (в вашем проекте)
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-placeholder

# Роутер (если не установлен)
npm install react-router-dom
```

Добавить в роутер:
```tsx
import { EditorShell } from "./editor/EditorShell";
import { EditorMetaProvider } from "./editor/editorMetaContext";

// В провайдере:
<EditorMetaProvider>
  <Route path="/editor" element={<EditorShell />} />
  <Route path="/editor/:essayId" element={<EditorShell />} />
</EditorMetaProvider>
```

`.env` фронтенда:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Переменные окружения

| Переменная | Описание | Дефолт |
|---|---|---|
| `MISTRAL_API_KEY` | API ключ Mistral | `""` (фолбэк-режим) |
| `MISTRAL_MODEL` | Модель | `mistral-large-latest` |
| `DATABASE_URL` | asyncpg строка | `postgresql+asyncpg://…` |
| `CORS_ORIGINS` | Разрешённые origins | `http://127.0.0.1:5173` |
| `VITE_API_BASE_URL` | Бэкенд URL для фронтенда | `http://127.0.0.1:8000` |

---

## Ключевые зависимости фронтенда

| Пакет | Зачем |
|---|---|
| `@tiptap/react` | Rich text editor |
| `@tiptap/starter-kit` | Базовые расширения TipTap |
| `@tiptap/extension-placeholder` | Плейсхолдер в пустом редакторе |
| `react-router-dom` | Роутинг (`useParams`, `useNavigate`) |

---

## Что НЕ включено в этот модуль

- Dashboard, Training, EssayHistory — отдельные модули
- Wörterbuch (iframe) — статическая страница, отдельно
- Alembic-миграции — нужно скопировать из `backend/alembic/`
- Данные `.topic.yaml` — из `data/topics/`
- Webp-кисти для словарных компонентов — из `frontend/public/assets/wordlist/`
