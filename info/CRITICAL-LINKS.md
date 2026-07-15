# CRITICAL-LINKS — карта зависимостей (не ломать!)

> **Создан:** 2026-07-04  
> **Цель:** безопасная уборка техдолга. Перед удалением/переименованием любого файла — проверь этот документ.  
> **Production-страницы:** `index.html`, `schreiben.html`, `pipeline.html`  
> **Удалено 2026-07-04:** `editor.html` + `js/editor*.js` + `css/editor.css` + `autumn.png`

---

## 1. Страницы → ассеты → API

```
index.html   — переводчик-поиск (слева) + личный список слов (справа)
├── css/site-header.css, css/styles.css
├── js/site-header.js, js/words-data.js, js/app.js, js/animations.js
├── images/abstract-watercolor-column.png   (styles.css .bg-column)
├── images/decor-head.png                   (styles.css mask)
├── images/Verwendung.png, Deklination.png  (styles.css CSS vars)
├── worte/*.png                             (words-data.js brushOfCard → строки)
└── API (все — /api/vocab/*, см. §6b):
    ├── GET    /api/vocab/search?q=          (поиск, публичный)
    ├── GET    /api/vocab/entry/{lemma}      (полная карточка, публичный)
    ├── GET    /api/vocab/list               (свои слова — ТРЕБУЕТ аккаунт)
    ├── GET    /api/vocab/list/stats         (донат)
    ├── POST   /api/vocab/list               (добавить)
    └── DELETE /api/vocab/list/{lemma}       (убрать)

`GET /api/words` (Postgres-таблица `words`, 17 seed-слов) страницей БОЛЬШЕ НЕ
используется — канон это обогащённые карточки. Роут жив, его зовёт только
`editor.js`, которого тоже нет. Кандидат на удаление отдельным заходом.

schreiben.html
├── css/site-header.css, css/schreiben.css
├── js/site-header.js, js/words-data.js, js/schreiben-api.js
├── js/analysis-waiting-phrases.js, js/schreiben.js
├── images/background_schreiben.png         (body bg)
├── images/timer-wash.png, tool-card-wash.png
├── images/kli-1/2/3.png, decor-head.png, Deklination.png
├── images/tool-hilfen.png, tool-woerterbuch.png  (HTML <img>)
├── images/roadmap-leaf-1/2/3.png           (schreiben.js LEAF_SPOTS)
├── worte/*.png                             (words-data.js brushOf)
└── API: owner-scoped /api/essays + /versions + /analyses (schreiben-api.js)
    localStorage: offline dirty copy/cache (ключ `deutschEssay.schreiben.v1`)

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

| Откуда | Essay | Pipeline | Wörterbuch |
|--------|-------|----------|------------|
| `index.html` | `schreiben.html` | `pipeline.html` | self (active) |
| `schreiben.html` | self (active) | `pipeline.html` | `index.html` |
| `pipeline.html` | `schreiben.html` | self (active) | `index.html` |

Все три страницы используют одну открытую editorial-навигацию из
`css/site-header.css`; она ссылается на `images/header/*.png`, а контекстный
Pomodoro отображается только на Essay.

---

## 2. Shared data — WASH (единый источник)

**КРИТИЧНО:** `js/words-data.js` — единственное место для `WASH`. Любое переименование `worte/*.png` → обновить только этот файл.

| Файл | Роль |
|------|------|
| `js/words-data.js` | WASH, typeKey, brushOf, **brushOfCard**, ~~PIPELINE_WASHES~~ |
| `js/app.js` | Wörterbuch: поиск + личный список (кисти через `brushOfCard`) |
| `js/schreiben.js` | demo WORDS + server-hydrated essay store (кисти через `brushOf`) |

**Маппинг WASH:** ключ = `{level}|{type}`, где level = `B1`|`B2`|`C1`, а type = `der`|`die`|`das`|`verb`|`adj`. Всего 15 кистей — новых не рисуем.

**Две функции, не путать (проверено 2026-07-15):**

- `brushOf(w)` — старая, для локальных объектов вида `{level:'B1', art:'die', pos:'noun'}`.
  Живой вызов ровно один: `js/schreiben.js:773`.
- `brushOfCard(card)` — для карточек из `/api/vocab/*`. Они приходят с уже
  готовыми `band` и `type`, потому что маппинг живёт на бэке
  (`backend/app/vocab/norm.py`) и общий для поиска, списка и доната — если
  посчитать его ещё и на фронте, две копии разъедутся.

**Клампинг уровней (backend `norm.LEVEL_BAND`):** в базе уровни `a1…c2` + `unlisted`,
а кистей только B1/B2/C1. Поэтому `a1,a2,b1 → B1`, `b2 → B2`, `c1,c2,unlisted → C1`.
`unlisted` — это ~70% базы (реальные слова вне списков Goethe), решение показывать
их как C1 принято владельцем. Части речи: `adv`/`other` → кисть `adj`;
существительное без артикля → тоже `adj` (это субстантивированные прилагательные,
der/die Jugendliche — у них артикль и правда не фиксирован).

**Устарело / мёртвое:**

- `PIPELINE_WASHES` — **не используется никем**. `pipeline.html` больше не грузит
  `words-data.js` (только `site-header.js`, `pipeline.js`, `enrich.js`).
  Раньше документ утверждал обратное.

---

## 3. Изображения — полная таблица ссылок

### Корень `images/` (4.1 MB, 16 PNG)

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

### `images/header/` (4 RGBA PNG)

| Файл | ~KB | Кто ссылается | Роль |
|------|-----|---------------|------|
| `header-wash-desktop.png` | 2388 | `site-header.css` | Широкий акварельный фон |
| `header-wash-mobile.png` | 2468 | `site-header.css` | Фон двухстрочной mobile-шапки |
| `header-flourish-right.png` | 2172 | `site-header.css` | Ботаническая композиция у инструментов |
| `nav-active-stroke.png` | 2028 | `site-header.css` mask | Акварельное подчёркивание активного раздела |

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
| **Header art** | все 4 файла `images/header/*.png` | `site-header.css` | фон, декор и mask с мягкой альфой |
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
docker-compose: postgres + backend + frontend (только публичные frontend mounts)
```

### API routes (backend/app/main.py)

| Router | Prefix | Кто вызывает |
|--------|--------|--------------|
| `health` | `/health` | nginx proxy; `editor-api.js` |
| `auth` | `/api/auth` | общий header |
| `essays` | `/api/essays` | `schreiben.js` |
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

1. **Единая шапка** — все три production-страницы подключают `site-header.css` и
   `site-header.js`. Essay-специфичные стили Pomodoro остаются в `schreiben.css`;
   не возвращать туда отдельную копию `.topbar` / `.nav`.

2. **Cache-bust `?v=N`** — при смене CSS/JS обновлять версию в HTML
   (`site-header.css` сейчас `?v=11`, `site-header.js` — `?v=8`,
   `schreiben.css` — `?v=28`, `styles.css` — `?v=24`, `app.js` — `?v=29`,
   `words-data.js` — `?v=2`).

3. **Frontend mounts** — при добавлении нового публичного корневого файла/каталога
   явно добавить его в `docker-compose.yml`; весь репозиторий намеренно не монтируется.

4. **schreiben localStorage** — теперь только offline dirty-копия; серверный список
   и owner scope каноничны, не возвращать localStorage в роль единственного источника.

5. **THEMEN в schreiben.js** — статика (12 тем). Pipeline DB темы пока не подключены.

6. **normalize_grammar_data()** — не вызывается при записи слов → грязная грамматика в БД.

7. **Удаление PNG до обновления CSS url()** — мгновенно ломает фоны/маски на всех страницах.

8. **WASH filename typo** — ключи жёстко привязаны к именам файлов в `worte/`. Одна опечатка = прозрачные карточки слов.

9. **Lossy WebP на ALPHA-ассетах** — все `worte/*.png`, watercolor, decor-head (mask), washes, leaves, tool-icons. Даёт видимые артефакты на полупрозрачных фонах. Только lossless PNG-opt или lossless WebP со сравнением.

10. **Docker Desktop macOS: устаревший bind-mount** — nginx может отдавать
    ОБРЕЗАННУЮ версию правленого файла (напр. `pipeline.html` без `<script>`), т.к.
    VirtioFS-кэш не инвалидируется после in-place правок. Симптом: браузер грузит
    страницу без JS, `document.scripts` пуст. Фикс: `docker compose up -d --force-recreate frontend`.
    Сверять: `docker compose exec frontend wc -l /usr/share/nginx/html/pipeline.html` vs host.

---

## 6a. Vocab-обогащение (`/api/vocab/enrich/*`) — актуальный контур

Серверные воркеры (один на аккаунт) обогащают `vocab.db` через Mistral и пишут
карточки в `enrichment.db`. Реальные БД — `backend/app/vocab/vocab_data/` (docker-mount
`VOCAB_DB=/app/vocab_data/vocab.db`), НЕ корневые `vocab.db`/`enrichment.db` (устаревшие пустышки).

| Endpoint | Auth | Кто вызывает |
|----------|------|--------------|
| `GET  /api/vocab/enrich/progress` | нет | `js/enrich.js` (poll 2.5s) |
| `GET  /api/vocab/enrich/cards`    | нет | `js/enrich.js` — браузер обогащённых карточек |
| `GET  /api/vocab/enrich/card/{lemma}` | нет | `js/enrich.js` — деталь карточки |
| `POST /api/vocab/enrich/requeue`  | **да** | `js/enrich.js` — переобогатить low-confidence |
| `POST /api/vocab/enrich/{start,stop}` | **да** | привязанный ключ аккаунта |

- **Мусор-фильтр**: `enrich.JUNK_SQL`/`is_junk()` — леммы с дефисом (`mit-`, `a-`),
  all-caps (`DER`, `ER`), 1 символ НИКОГДА не отдаются воркеру (считаются `junk` в progress).
- **LLM-skip**: модель может вернуть `skip:true` для не-слов (Eigennamen, аббревиатуры,
  капс-дубли) → терминальный статус `skipped`, не карточка. Бампать `PROMPT_VERSION` при правке промпта.
- **ru_all** — массив переводов (основное первым); карточка = `enrichment.db.cards.data` (JSON).
- **Мульти-устройство (LAN)**: работает по http из коробки — cookie `secure=False`+`SameSite=lax`,
  запросы same-origin через nginx, воркеры по `user_id` не конфликтуют (атомарный `claim`).
  CORS расширен regex'ом на приватные подсети (`main.py` `LAN_ORIGIN_RE`). `secure_cookies`
  держать `False` для http-LAN; каждое устройство — свой аккаунт + свой ключ Mistral.

---

## 6b. Wörterbuch — поиск + личный список (2026-07-15)

Страница `index.html` переписана: слева переводчик-поиск по базе, справа личный
список слов на заучивание. Канон — **обогащённые карточки**, не Postgres `words`.

### Зеркало: зачем оно есть

Воркер обогащения владеет `enrichment.db` (SQLite) и пишет туда круглосуточно —
трогать его нельзя. Но нечёткий поиск (`pg_trgm`) и личный список должны
джойниться, то есть жить в одной БД. Поэтому готовые карточки **копируются** в
Postgres. Обратно не пишем никогда, SQLite открывается read-only.

```
enrichment.db (SQLite, WAL)  --read-only-->  app/vocab/mirror.py
                                                   |
                                                   v
                             Postgres: vocab_cards + vocab_card_translations
                                                   |
                          app/vocab/search.py (pg_trgm)  <--  /api/vocab/search
                                                   |
                             Postgres: user_word_list  <--  /api/vocab/list
```

- Курсор синхронизации — пара `(created_at, lemma)`. `save_cards` пишет через
  `INSERT OR REPLACE` со свежим `created_at`, поэтому переобогащённая карточка
  сама всплывает в конце курсора: апдейты едут тем же путём, что и вставки.
- Синхронизация запускается на старте контейнера и раз в 5 мин
  (`mirror.periodic_sync`, поднимается в `main.py` on_startup). Ручной пинок —
  `POST /api/vocab/mirror/sync`.
- Зеркало **производное**: его можно дропнуть и пересобрать за ~15 сек.
  `user_word_list` — НЕТ, это данные пользователя.

### Поиск

- Раскладка решает язык: латиница → немецкая лемма, кириллица → `ru_all`.
- **Две нормализованные колонки** на немецкой стороне: `lemma_norm` (grün→gruen)
  и `lemma_ascii` (grün→grun). Обе индексируются GIN/trigram и обе всегда
  участвуют в запросе. Одной мало: у запроса «grun» умляутов нет, обе его свёртки
  совпадают — но само слово хранится по-разному, и без `lemma_ascii` «grün»
  не находится вовсе (проверено: выше него встают Grund и Grunzen).
- Русская морфология вытягивается триграммами без стеммера
  (`зависимостью`→`зависимость` = 0.79 при пороге 0.3).
- Ничего не нашли → так и говорим. База ещё обогащается, выдавать вместо ответа
  случайные близкие слова — хуже честного «нет».

### Ключ личного списка

`user_word_list` адресует слово **строкой `lemma`**, без FK на `vocab_cards`:
промпт обогащения уже разводит омографы регистром (Morgen/morgen, Essen/essen),
а будущее расширение будет слать слова с произвольных страниц, которых в базе
может не быть. Колонки-снимок (`ru`, `band`, `pos`, …) нужны, чтобы список
рисовался одним запросом.

> ⚠️ Снимок — это только то, что нужно СТРОКЕ. В нём нет `definition_de`,
> `grammar`, `examples`. Карточку из списка открывать **только** через
> `GET /api/vocab/entry/{lemma}`, иначе отрисуется пустышка.

### Аккаунт

Список требует аккаунт: `require_user`, гостевого режима нет (в отличие от эссе).
Вход переиспользует готовый диалог из `js/site-header.js` (`window.SiteAuth`,
событие `site-auth-change`) — своей формы на странице нет.

### Карточка-оверлей

Открывается поверх колонки, **противоположной** слову: слово в поиске (слева) →
карточка накрывает список справа, и наоборот. Так слово остаётся на экране и к
нему можно тянуть оранжевый коннектор (`#linkLine`). `.card-layer::before` гасит
накрытую колонку — без него из-под карточки торчит кисть строки (она вылезает
за свою строку на 10px) и это читается как баг.

Линия рисуется **синхронно** в `showCard`, не через `requestAnimationFrame`:
в фоновой вкладке rAF не вызывается вообще, и карточка осталась бы без связи.

---

## 8. Порядок работ (рекомендуемый)

```
Фаза 0  ✅ CRITICAL-LINKS.md
Фаза 1  ~~Сжатие~~ — отменено (alpha-ассеты)
Фаза 2  ✅ js/words-data.js — единый WASH
Фаза 3  schreiben.js → /api/words, /api/essays (замена localStorage)
Фаза 4  ✅ editor.* + autumn.png + screenshots/ удалены
Фаза 5  ✅ Alembic (backend/alembic/) + uv/pyproject + Makefile + единый backend/.env (2026-07-10)
Фаза 6  Backend: pipeline v2/v3 unify, normalize on write
Фаза 7  ✅ Wörterbuch: переводчик-поиск (pg_trgm) + личный список (2026-07-15), см. §6b
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
