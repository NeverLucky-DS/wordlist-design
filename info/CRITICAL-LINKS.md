# CRITICAL-LINKS — карта зависимостей (не ломать!)

> **Создан:** 2026-07-04  
> **Цель:** безопасная уборка техдолга. Перед удалением/переименованием любого файла — проверь этот документ.  
> **Production-страницы:** `index.html`, `schreiben.html`, `pipeline.html`  
> **Удалено 2026-07-04:** `editor.html` + `js/editor*.js` + `css/editor.css` + `autumn.png`

---

## 1. Страницы → ассеты → API

```
index.html
├── css/site-header.css, css/styles.css
├── js/site-header.js, js/words-data.js, js/app.js, js/animations.js
├── images/abstract-watercolor-column.png   (styles.css .bg-column)
├── images/decor-head.png                   (styles.css mask)
├── images/Verwendung.png, Deklination.png  (styles.css CSS vars)
└── worte/*.png                             (words-data.js brushOf → word list)
    └── GET /api/words?limit=500            (app.js loadApiWords — merge в WORDS)

schreiben.html
├── css/schreiben.css
├── js/site-header.js, js/words-data.js, js/schreiben.js
├── images/background_schreiben.png         (body bg)
├── images/timer-wash.png, tool-card-wash.png
├── images/kli-1/2/3.png, decor-head.png, Deklination.png
├── images/tool-hilfen.png, tool-woerterbuch.png  (HTML <img>)
├── images/roadmap-leaf-1/2/3.png           (schreiben.js LEAF_SPOTS)
├── worte/*.png                             (words-data.js brushOf)
└── API: POST/PATCH /api/essays + POST …/analyze/stream (schreiben-api.js)
    localStorage: drafts, snapshots, report cache (ключ `deutschEssay.schreiben.v1`)

pipeline.html
├── css/site-header.css, css/pipeline.css
├── js/site-header.js, js/words-data.js, js/pipeline.js
├── images/abstract-watercolor-column.png   (pipeline.css)
├── worte/*.png (PIPELINE_WASHES в words-data.js)
└── API (через nginx proxy /api/*):
    ├── GET  /api/pipeline/overview   (poll 3–9s)
    ├── GET  /api/pipeline/runs
    ├── GET  /api/pipeline/queue
    ├── POST /api/pipeline/queue        { topics: [...] }
    ├── POST /api/pipeline/run          { topic, article_urls: [] }
    └── GET  /api/pipeline/run/{id}     (детали ошибок)
```

### Навигация между страницами

| Откуда | Schreiben ведёт на | Wörterbuch | Pipeline |
|--------|-------------------|------------|----------|
| `index.html` | `schreiben.html` ✅ | self | `pipeline.html` |
| `schreiben.html` | `#` (active) | `index.html` | `pipeline.html` |
| `pipeline.html` | `schreiben.html` ✅ | `index.html` | self |

---

## 2. Shared data — WASH (единый источник)

**КРИТИЧНО:** `js/words-data.js` — единственное место для `WASH`, `brushOf`, `PIPELINE_WASHES`. Любое переименование `worte/*.png` → обновить только этот файл.

| Файл | Роль |
|------|------|
| `js/words-data.js` | WASH, typeKey, brushOf, PIPELINE_WASHES |
| `js/app.js` | WORDS + API merge (index) |
| `js/schreiben.js` | demo WORDS + essay store (localStorage) |

**Маппинг WASH:** ключ = `{level}|{type}` где type = `der`|`die`|`das`|`verb`|`adj`.

---

## 3. Изображения — полная таблица ссылок

### `images/` (4.1 MB, 16 PNG)

| Файл | ~KB | Кто ссылается | Production? |
|------|-----|---------------|-------------|
| `background_schreiben.png` | 896 | `schreiben.css` body | ✅ schreiben |
| `autumn.png` | 864 | `editor.js` L1173 | ❌ editor only |
| `kli-1.png` | 420 | `schreiben.css`, `editor.css` | ✅ schreiben |
| `kli-2.png` | 420 | `schreiben.css`, `editor.css` | ✅ schreiben |
| `kli-3.png` | 356 | `schreiben.css`, `editor.css` | ✅ schreiben |
| `abstract-watercolor-column.png` | 288 | `styles.css`, `pipeline.css`, `editor.css` | ✅ index, pipeline |
| `Deklination.png` | 224 | `styles.css`, `schreiben.css` | ✅ index, schreiben |
| `Verwendung.png` | 204 | `styles.css`, `editor.css` | ✅ index |
| `tool-card-wash.png` | 180 | `schreiben.css` | ✅ schreiben |
| `timer-wash.png` | 160 | `schreiben.css` | ✅ schreiben |
| `tool-woerterbuch.png` | 56 | `schreiben.html` L166 | ✅ schreiben |
| `roadmap-leaf-1.png` | 48 | `schreiben.js` LEAF_SPOTS | ✅ schreiben |
| `roadmap-leaf-2.png` | 44 | `schreiben.js` LEAF_SPOTS | ✅ schreiben |
| `tool-hilfen.png` | 20 | `schreiben.html` L154 | ✅ schreiben |
| `roadmap-leaf-3.png` | 20 | `schreiben.js` LEAF_SPOTS, MID_LEAVES | ✅ schreiben |
| `decor-head.png` | 8 | `styles.css`, `schreiben.css`, `editor.css` | ✅ index, schreiben |

### `worte/` (2.4 MB, 15 PNG) — все 15 используются через WASH

Все 15 brush-файлов нужны для `index` + `schreiben`. `pipeline` использует 8 из них в `WASHES[]`.

### `screenshots/` (1.3 MB) — только README, **можно удалить** без поломки UI

---

## 4. Оптимизация изображений — ⚠️ прозрачность

**Правило (от владельца проекта):** большинство PNG **нельзя** гонять через lossy WebP — на них альфа-канал / мягкие края акварели. Lossy WebP на прозрачности даёт ореолы, грязные края, ломает CSS `mask` и полупрозрачные `background-image`.

### Классификация (проверено Pillow, 2026-07-04)

#### 🔴 ALPHA — оставить PNG, lossy WebP запрещён

| Группа | Файлы | Где | Почему опасно |
|--------|-------|-----|---------------|
| **Кисти** | все 15 `worte/*.png` | `app.js`, `schreiben.js`, `pipeline.html` WASHES | CSS `background-image` + `opacity` в CSS — любой артефакт виден на карточках слов |
| **Декор** | `abstract-watercolor-column.png` | index, pipeline, editor CSS | мягкая акварель по краю |
| **Маска** | `decor-head.png` | CSS `-webkit-mask` / `mask` | WebP-lossy ломает маску → детальная карточка без «головы» |
| **Washes** | `timer-wash.png`, `tool-card-wash.png` | `schreiben.css` | полупрозрачные подложки |
| **Иконки** | `tool-hilfen.png`, `tool-woerterbuch.png` | `schreiben.html` | RGBA |
| **Листья** | `roadmap-leaf-1/2/3.png` | `schreiben.js` | RGBA, анимация на roadmap |

**Безопасные альтернативы для ALPHA:** `oxipng -o2` / `pngcrush` (lossless), или `pngquant` с `--quality` (сохраняет альфу лучше WebP-lossy). WebP только **lossless** — и то сравнить визуально.

#### 🟢 Opaque — можно lossy WebP (единственные реальные кандидаты)

| Файл | ~KB | Кто | Комментарий |
|------|-----|-----|-------------|
| `background_schreiben.png` | 896 | `schreiben.css` body | RGB, без альфы — **главный выигрыш** |
| `kli-1/2/3.png` | 420+420+352 | `schreiben.css` ::after | mode=P, без transparency index — проверить визуально после сжатия |
| `Deklination.png` | 221 | `styles.css`, `schreiben.css` | opaque, но фон detail-блока — осторожно |
| `Verwendung.png` | 201 | `styles.css` | opaque |
| `autumn.png` | 861 | `editor.js` only | editor скорее убираем |

#### Итого по объёму

| Категория | ~размер | Стратегия |
|-----------|---------|-----------|
| ALPHA (worte + washes + decor) | ~3.5 MB | PNG lossless optimize, **не** lossy WebP |
| Opaque large | ~2.5 MB | WebP quality 80–85 или pngquant |
| screenshots/ | 1.3 MB | удалить (не в UI) |

### Если всё же WebP — чеклист ссылок

Обновить **каждую** ссылку только для тех файлов, что реально конвертировали:

```
CSS:  styles.css, schreiben.css, pipeline.css
HTML: schreiben.html (2× <img> — только если иконки трогали)
JS:   app.js, schreiben.js, pipeline.html inline WASHES[]
nginx.conf: добавить webp в cache location
```

**Порядок:** конвертировать → обновить ссылки → smoke-test 3 страницы → удалять PNG.

**Не делать:** массовый `*.png → *.webp` по папкам `worte/` и `images/` без проверки альфы.

---

## 5. Backend — что трогать осторожно

```
nginx :8753  →  proxy /api/*, /health  →  FastAPI :8000
docker-compose: postgres + backend + frontend (mount всего репо в nginx!)
```

### API routes (backend/app/main.py)

| Router | Prefix | Кто вызывает |
|--------|--------|--------------|
| `health` | `/health` | nginx proxy; `editor-api.js` |
| `essays` | `/api/essays` | **только editor** |
| `words` | `/api/words` | `app.js`, `editor.js` |
| `phrases` | `/api/phrases` | **только editor** |
| `topics` | `/api/topics` | никто на фронте |
| `pipeline` | `/api/pipeline/*` | `pipeline.html` inline |

### Pipeline backend chain (production-critical)

```
POST /api/pipeline/queue
  → scheduler.py (если pipeline_autorun=true)
  → runner.py
      → discovery.py (Grok/DDG)
      → extraction.py
      → enrichment.py (Mistral batch)
      → supplement.py
      → normalize.py (НЕ вызывается на write! — баг)
```

**v2 vs v3 split:** `content_llm.py`, `verify.py` — только в `backend/scripts/`, НЕ в runner. Не удалять пока не унифицировано.

### DB tables (pipeline-related)

`words`, `phrases`, `word_topics`, `pipeline_runs`, `topic_queue_items`, `word_failures`

`index.html` читает `words` через API. `schreiben.html` пока **не** читает — статический `THEMEN` + demo `WORDS`.

---

## 6. Файлы — что можно убирать / что нельзя

### 🟢 Относительно безопасно удалить

| Путь | Почему |
|------|--------|
| `screenshots/` | Только README |
| `images/autumn.png` | Только editor (если editor убираем) |
| `info/AUDIT.md` | Документация (не runtime) |

> `PIPELINE.md` удалён 2026-07-06 — заменён на `info/pipeline.md`.

### 🟡 Убрать после проверки

| Путь | Зависимости |
|------|-------------|
| `editor.html` | `editor.js`, `editor-api.js`, `editor.css`, `autumn.png` |
| `js/editor.js` | 1593 строк, API essays/phrases/analyze |
| `js/editor-api.js` | Только editor |
| `css/editor.css` | Только editor |
| `js/animations.js` | Только `index.html` — **НЕ удалять** пока index жив |

### 🔴 НЕ трогать без полного аудита

| Путь | Почему |
|------|--------|
| `js/app.js` | index word grid + API merge + WASH |
| `js/schreiben.js` | Весь schreiben UI + localStorage store |
| `js/site-header.js` | index + pipeline (theme toggle) |
| `worte/*.png` | 3 JS-файла + pipeline inline |
| `backend/app/pipeline/runner.py` | Production pipeline |
| `backend/app/db/models.py` | Schema для всего |
| `nginx.conf` | API proxy + cache rules |
| `docker-compose.yml` | Dev stack |

---

## 7. Известные ловушки (ломались бы при наивной уборке)

1. **schreiben без site-header.js** — свой topbar в CSS, не shared header JS. Theme toggle на schreiben — только HTML-кнопка без логики? (проверить: `#themeBtn` в schreiben — нет site-header.js!)

2. **Cache-bust `?v=N`** — при смене CSS/JS обновлять версию в HTML (`index.html` styles `?v=21`, schreiben `?v=10`).

3. **docker mount `.:/usr/share/nginx/html`** — nginx отдаёт **весь репо** включая `backend/`, `.git`. Только local dev.

4. **schreiben localStorage** vs **editor API** — два несовместимых essay flow. Удаление editor ≠ замена schreiben на API.

5. **THEMEN в schreiben.js** — статика (12 тем). Pipeline DB темы пока не подключены.

6. **normalize_grammar_data()** — не вызывается при записи слов → грязная грамматика в БД.

7. **Удаление PNG до обновления CSS url()** — мгновенно ломает фоны/маски на всех страницах.

8. **WASH filename typo** — ключи жёстко привязаны к именам файлов в `worte/`. Одна опечатка = прозрачные карточки слов.

9. **Lossy WebP на ALPHA-ассетах** — все `worte/*.png`, watercolor, decor-head (mask), washes, leaves, tool-icons. Даёт видимые артефакты на полупрозрачных фонах. Только lossless PNG-opt или lossless WebP со сравнением.

---

## 8. Порядок работ (рекомендуемый)

```
Фаза 0  ✅ CRITICAL-LINKS.md
Фаза 1  ~~Сжатие~~ — отменено (alpha-ассеты)
Фаза 2  ✅ js/words-data.js — единый WASH
Фаза 3  schreiben.js → /api/words, /api/essays (замена localStorage)
Фаза 4  ✅ editor.* + autumn.png + screenshots/ удалены
Фаза 5  Backend: pipeline v2/v3 unify, Alembic, normalize on write
```

---

## 9. Smoke-test после любых изменений

```bash
# Backend + frontend
docker compose up -d

# Открыть и проверить:
open http://localhost:8753/index.html      # слова, кисти, detail card, API merge
open http://localhost:8753/schreiben.html  # roadmap, tools, bg, leaves, pomodoro
open http://localhost:8753/pipeline.html     # overview poll, queue, shelf tiles

# API health
curl -s http://localhost:8753/health
curl -s http://localhost:8753/api/pipeline/overview | head
curl -s http://localhost:8753/api/words?limit=3
```

**Визуально проверить:** watercolor-колонка слева, brush-фоны на словах, фон schreiben, листья roadmap, tool-иконки, tile-washes на pipeline shelf.

---

*Обновлять этот файл при каждом рефакторинге, который меняет ссылки или удаляет файлы.*
