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

**`band` — ключ кисти, `freq` — то, что показывается пользователю (2026-07-19).**
`unlisted` вырос до **95.6 %** (88 067 из 92 090), то есть CEFR-бейдж почти на
каждой строке был заглушкой. Теперь `card_out` отдаёт ещё и
`freq` = `haeufig|mittel|selten|null` (`norm.freq_of`, порог häufig 4.0 —
там центр B1-лексики Goethe, медиана 4.16), а `js/app.js levelChip()` рисует
настоящий уровень тем 4 023, у кого он есть, и частотность всем остальным.

⚠️ **`band` при этом НЕ трогали** — он по-прежнему CEFR-образный и по-прежнему
выбирает кисть. Кистей 15, новых не рисуем; пересадить их на частотность значит
переписать весь визуальный язык страницы.

⚠️ **Частотность нельзя показывать как уровень, и стили это держат.** Проверено
на 4 023 карточках с разметкой Goethe: при лучшем пороге промах 12 % B1-слов и
36 % C1-слов, а B1 от B2 частотность не отличает вовсе (4.16 против 4.15).
Поэтому `.lvl-tag.is-cefr` в рамке (цитирует опубликованный список), а
`.lvl-tag.is-freq` тихий, без рамки, с точкой — это наше чтение корпуса.
Сделать их одинаковыми = вернуть ту же ложь в новом шрифте.

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
   `schreiben.css` — `?v=28`, `styles.css` — `?v=28`, `app.js` — `?v=33`,
   `words-data.js` — `?v=2`, `pipeline.css` — `?v=8`, `enrich.js` — `?v=5`).

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
| `GET  /api/vocab/enrich/fleet` | **админ** | `js/enrich.js` — таблица аккаунтов |
| `POST /api/vocab/enrich/fleet/{start,stop}` | **админ** | `js/enrich.js` — весь флот разом |
| `GET  /api/vocab/enrich/cards`    | нет | `js/enrich.js` — браузер обогащённых карточек |
| `GET  /api/vocab/enrich/card/{lemma}` | нет | `js/enrich.js` — деталь карточки |
| `POST /api/vocab/enrich/requeue`  | **да** | `js/enrich.js` — переобогатить low-confidence |
| `POST /api/vocab/enrich/{start,stop}` | **да** | привязанный ключ аккаунта |

### Этапы прогона (одна кнопка — несколько видов работы, 2026-07-17)

`POST /api/vocab/enrich/start` сначала зовёт `enrich_worker.ensure_planned()`
(один раз на процесс) → `enrich.plan_repairs()`, и только потом стартует воркер.

Фаза — это **тег в `word_status.phase`, а не координатор**: `claim` просто отдаёт
работу из самой приоритетной фазы, где ещё что-то осталось. Поэтому 10 аккаунтов
не нуждаются в выборе лидера — они читают одну таблицу и сходятся сами.

Порядок — из `enrich.PHASES`; починки идут перед backfill намеренно (они меньше и
проверяют матчер ответов на известных словах за минуты, а не в 4 утра).

| # | phase | что чинит | размер / осталось (2026-07-18) |
|---|-------|-----------|-------------------------------|
| 1 | `repair_pairs` | пары, убитые фолдингом регистра в `parse_response` | 1343 / 176 |
| 2 | `repair_case` | омографы, склеенные фолдингом регистра | 1231 / 4 |
| 3 | `repair_ortho` | дореформенные написания, умершие в `failed` | 456 / 52 |
| 4 | `repair_split` | расклейка нескольких значений, скрамленных в `ru_all` | 1324 / 39 |
| 5 | `backfill` | обычная выдача (нетегированные слова) | 102 903 / 0 |

Backfill выбран до конца: из 108 084 лемм `vocab.db` в `word_status` доехали
107 257 (остальное отсеял мусор-фильтр), и ни одна не ждёт выдачи.

**`plan_repairs()` идемпотентен через самоограничение**: слово тегируется, только
пока оно `phase` NULL/backfill. После тега тег остаётся навсегда, каким бы ни был
исход, — поэтому починка, которую модель отвергла или которая снова дала
одинаковые карточки, делается один раз и не зацикливается на каждом старте.
Проверено на живой базе: 0.7–3.5 s, повтор даёт нули.

Ещё `plan_repairs` добивает `cards.zipf` из `vocab.db` (UPDATE на месте). Курсор
зеркала это НЕ видит (`created_at` не двигается), поэтому старт разово запускает
`mirror.full_resync()` — ~30 s на 64k, поиск при этом продолжает работать.

- **Мусор-фильтр**: `enrich.JUNK_SQL`/`is_junk()` — леммы с дефисом (`mit-`, `a-`),
  all-caps (`DER`, `ER`), 1 символ НИКОГДА не отдаются воркеру (считаются `junk` в progress).
- **LLM-skip**: модель может вернуть `skip:true` для не-слов (Eigennamen, аббревиатуры,
  капс-дубли) → терминальный статус `skipped`, не карточка. Бампать `PROMPT_VERSION` при правке промпта.
  `skip_words()` **удаляет** уже существующую карточку: на повторном проходе модель
  пересуживает то, что мы уже опубликовали (напр. существительное, ошибочно
  записанное под `nacht`), и оставлять его в поиске нельзя. Ничего не теряется
  навсегда — `vocab.db` неизменяем, requeue обогащает лемму заново.
- **Сопоставление ответа (`parse_response`) — точное по имени, регистр НЕ фолдится.**
  Так было не всегда: индекс строился по `word.lower()`, и обе половины пары,
  посланной одним батчем, получали ОДНУ карточку. 635 пар в базе оказались
  побайтово одинаковыми, `morgen`=завтра не существовало вовсе (запрос «завтра»
  выдавал Frühstück). Регистр — единственное, что различает эти слова.
  Фолдированный фоллбэк (`norm.fold_de`) есть, но только для ß/ss и только когда
  свёртка однозначна с ОБЕИХ сторон, — пара Morgen/morgen до него не доходит.
- **Переименование на современную орфографию**: модели разрешено вернуть в `word`
  написание после реформы 1996 (`Schluß`→`Schluss`). Тогда `save_cards(renamed=…)`
  кладёт КАРТОЧКУ под новую лемму, а `word_status` остаётся на посланной — иначе
  слово выглядело бы необогащённым и выдавалось бы вечно. Проверено живым вызовом:
  `Schluß→Schluss`, `Bewußtsein→Bewusstsein`, а `Straße` (ß после долгого гласного)
  не тронута. В базе 3371 ß-лемма и лишь у 16 есть ss-двойник — это добавляет
  современное написание, а не затирает существующее.
- **ru_all** — массив переводов (основное первым); карточка = `enrichment.db.cards.data` (JSON).

### Вливание новых слов (`vocab/intake.py`, 2026-07-19)

Покрытие впервые померено **на внешнем тексте**, а не на самой базе: 18 полных
статей de.wikipedia ровно по темам Goethe Schreiben, 21 114 токенов. Из 1 088
промахов zipf ≥ 3.0 — **895 (82 %) отсутствуют в `vocab.db` вовсе**, и лишь 193
это брак обогащения. **Узкое место — источник, а не модель.**

Источник — дампы словарей до 1995 года, поэтому в нём есть `Kolchos` и
`Fernschreiber`, но нет `Internet` (zipf 5.23), `online`, `Digitalisierung`,
`Klimawandel`, `Smartphone`, `Privatsphäre`, `Suchmaschine`. Ни одно из них не
было даже кандидатом — их нет в `word_status`. Для тренажёра эссе, у которого
цифровизация и защита данных это и есть темы, это центральный пробел.

`claim` выдаёт работу из `v.words`, то есть **`vocab.db` — таблица вливания**.
Значит новое слово становится кандидатом просто дописыванием строки туда, и
остальной конвейер (мусор-фильтр, батчинг, промпт, skip-правила, зеркало) не
меняется вообще. Строки помечены `sources=["wiktionary"]` — это и подсказка
модели об источнике, и возможность откатить вливание одним DELETE.

Запуск офлайновый: `backend/scripts/import_new_words.py` (`--dry-run`,
`--min-zipf`, `--limit`, `--backup`).

**Прогон 2026-07-19: порог 1.75, влито 20 074 слова, `vocab.db` 108 084 →
128 158.** Порог выбран владельцем ради объёма. Как редеет материал:

| zipf ≥ | слов | что в полосе |
|---|---|---|
| 2.5 | 8 519 | `Internet`, `E-Mail`, `chatten`, `googeln`, `Klimawandel` |
| 2.0 | 15 564 | + `interkulturell`, `Paternalismus`, `Mindmap` |
| **1.75** | **20 074** | + `Sumerisch`, `Boa constrictor`, `Eichenprozessionsspinner` |

Отфильтроваться до «чистых 20 тысяч» **нельзя, проверено**: тематические метки
Wiktionary есть лишь у 15 % кандидатов, а фильтр по тегам регистра/региона
ловит 370 из 20 074 и при этом забирает нужные (`Streitkraft`, `Islamist`,
`Schurkenstaat`, `Nerd`). Низ полосы отсекается ниже по течению — skip-правилом,
`register`, пометкой форм и ранжированием по zipf, — а не на входе.

Откат: `DELETE FROM words WHERE sources='["wiktionary"]'` плюс `vocab.db.bak`.

> ⚠️ **Многословные записи отсекаются на входе.** Первый импорт пропустил 922
> штуки, и верх списка по частоте — спрягаемые формы фраз в ОБОИХ порядках:
> `war dabei` и `dabei war`, `bin dabei` и `dabei bin`, `ist dafür`. В старой
> базе многословных лемм было **ровно 0 на 108 084 строки**, то есть это
> инвариант, на который молча опираются карточка, личный список и подбор кисти.
> Полезные из них (`von Zeit zu Zeit`, `recht haben`) — это коллокации и идиомы,
> и под них в схеме карточки уже есть поля. Удалено, итог вливания — **19 152**.

### Грамматика по частям речи — `_GRAMMAR_KEYS` решает всё

`_norm_grammar` оставляет **только** ключи, перечисленные в `_GRAMMAR_KEYS` для
данной части речи. Чего там нет — выбрасывается молча, что бы модель ни вернула.

Так и потерялась грамматика наречий: ключа `adv` не существовало, и пусто
оказалось у **1 271 наречия из 1 271**. Замер 2026-07-19 по остальным: noun 3
из 55 822, verb 0 из 8 882, adj 387 из 9 811 (корректно — `tot`, `schwanger`
не степенуются), `other` 546 из 571.

Добавлять ключ надо **в двух местах сразу**: в `_GRAMMAR_KEYS` (иначе ответ
отбросится) и в GRAMMATIK-TABELLE промпта (иначе модель не узнает, что его
просят). Расхождение между ними воспроизводит ровно этот баг.

> ⚠️ **`VOCAB_DB` по умолчанию указывает на ПУСТЫШКУ.** Рядом с боевыми БД в
> `app/vocab/vocab_data/` лежат заглушки `app/vocab/vocab.db` и
> `enrichment.db`, и без переменной окружения (вне контейнера её нет никогда)
> путь резолвится в них. Первый dry-run прочитал именно их, получил `known = 0`
> и отрапортовал 36 455 «новых» слов, включая `Mensch` и `Software` — влей это
> не глядя, получили бы 36 тысяч дублей и счёт за уже готовые карточки. Теперь
> `known_lemmas` падает с явным сообщением, а скрипт печатает пути перед стартом.

> ⚠️ **`pos: "name"` — 9 % дампа.** Пустить имена собственные значило бы вернуть
> в базу ровно тот шум (Berlin, München, Peter), на вычистку которого skip-правило
> уже потратило токены. Отказываем сразу, вместе с аббревиатурами, аффиксами и
> фразами. Пускаем только noun/verb/adj/adv.

> ⚠️ **Знать надо не только `vocab.db`, но и `cards`.** Переименование на
> орфографию 1996 кладёт КАРТОЧКУ под новую лемму, а `word_status` оставляет на
> посланной: у `Fluss` карточка есть, а в `vocab.db` только `Fluß`. Проверка по
> одному `vocab.db` впустила бы `Fluss` как новое слово, оплатила бы его второй
> раз и дала бы `INSERT OR REPLACE` затереть хорошую карточку.

`form_of` здесь применяется, но **только в одну сторону** — отказать новому
слову, у которого ВСЕ значения формные. Это безопасно: отказавшись добавлять,
нельзя потерять существующую карточку. Опускать по нему уже имеющиеся карточки
по-прежнему нельзя (см. ниже про `morph.py`).

### Закрытый класс служебных слов (`vocab/funcwords.py`, 2026-07-19)

Тем же замером: `das` в базе есть, а `der`, `die`, `den`, `dem`, `des` — нет.
`die/den/dem` ушли в `skipped`, `der/des` — в `failed` после 3 попыток, оба
статуса терминальные. Так же потеряны `im`, `am`, `zum`, `zur`, `vom`, `beim`,
`ins`, `ans`, `aufs`, `fürs` и др., плюс `euch`, `denen`, `aller`, `wessen`.

Причина — правило про Wortform в промпте, и **правило право**: `die` это форма
`der`, `im` = `in dem`. На `ist`, `hat`, `war`, `meine` оно срабатывает верно —
там базовые леммы на месте. Промах только на закрытом классе, где «базовая
форма» это ячейка парадигмы, которую никто не ищет, а стяжение надо просто
знать (A1-грамматика, не выводится).

Поэтому 25 карточек **написаны руками**, `model='handwritten'`, ноль токенов.
Сеются из `plan_repairs()` — та же «одна кнопка», что и `zipf`/`forms`.

> ⚠️ **`requeue` обязан их пропускать.** `der`/`des` лежат в `failed`, а это
> ровно то, что собирает `repair_ortho`. Без защиты фаза вернула бы их модели,
> модель скипнула бы их по своему же правилу, а `skip_words` **удалил** бы
> карточку — закрытый класс исчезал бы снова через один прогон после посева.
> Барьер стоит в `requeue` (одно место на все фазы), тест —
> `test_repair_phases_cannot_requeue_a_handwritten_card`.

### Формы против заголовочных слов (`vocab/forms.py`, 2026-07-19)

`vocab.db` — дамп двуязычных словарей, а словарь перечисляет не только
заголовочные слова: там же лежат причастия (`gemacht`), множественные (`Fakten`),
формы претерита (`gäbe`), части сложных слов (`Schnell-` «в сл. сл.»),
сокращения и голые отсылки (`alleine` → «см. allein»). Обогащение не отличало их
от слов и сделало каждому карточку.

Само по себе не беда — беда в ранжировании. `wordfreq` **не различает регистр** и
считает словоформы, поэтому `Schnell` получает 5.51 прилагательного `schnell`, а
`gemacht` — вес всех «hat gemacht». Поиск читает `zipf` сразу после score, и
всплывает именно этот мусор: замер по живой базе — 16 % в полосе zipf 4–5 против
1 % ниже 2. Запрос «обманывать» отвечал `linken` (редкий разговорный глагол в
частотности прилагательного `link`), а `täuschen` и `betrügen` стояли под ним.

`tag_forms()` проставляет `cards.form_kind` + `cards.form_of`; поиск опускает
такие карточки ниже настоящих слов при равном score (`_by_relevance`), а UI
подписывает их «Form von machen» — как это делают Yandex.Dictionary и Linguee.
**Не удаляем**: `gemacht` по-прежнему находится, просто перестаёт выдавать себя
за слово.

**Сигнал — от лексикографа, не от нас.** Каждый маркер это заявление самого
словаря. Соблазнительная альтернатива — прогнать лемматизатор и выкинуть всё, что
свернулось, — неверна: `simplemma` даёт `bitte`→`bitten`, `danke`→`danken`,
`später`→`spät`, `weiß`→`wissen`, а это нужные слова. Лемматизатор не видит
лексикализации; словарь её уже увидел. `simplemma` тут только отвечает «форма ОТ
чего», но никогда не решает, что перед нами форма.

> ⚠️ **Позиция маркера решает всё.** Словарь открывает статью формы словами
> «part II от machen», но он же дописывает заметку о сложных словах в КОНЕЦ
> обычной длинной статьи: у `Tag` «Tag- дневной в сл. сл.» стоит на символе 8566
> из 8603. Поиск подстроки по всему телу пометил 1006 слов как части сложных,
> хотя их ~22, и в жертвы попали `Hand`, `Weg`, `Tag`, `Tod`, `Grund`, `Welt`,
> `Höhe`, `Art`. Отсюда `_MARKER_HEAD = 40` (маркер обязан открывать статью) плюс
> для `compound` — тело начинается с `{лемма}-`. Проверено: ни одна «глубокая»
> статья этот тест не проходит.

Итог на живой базе: 1676 карточек — inflection 1412, capitalised 194, abbrev 22,
compound 22, variant 26. Проход ~4 s, идемпотентен, тег снимается, если правило
перестало срабатывать (иначе исправленный ложняк остался бы опущенным навсегда).

### Парадигмы из Wiktionary (`vocab/morph.py`, 2026-07-19)

Модель пишет в `data.grammar` три поля на глагол и два на существительное —
достаточно опознать слово и мало чтобы им пользоваться. Настоящего времени нет
вовсе, то есть `du gibst` / `er gibt` (чередование, которое дрессируют на A2–B1)
в базе не было ни у одного глагола. У существительных был генитив и множественное,
но не датив — а это прячет n-Deklination: `Student` хранил «des Studenten / die
Studenten», и «dem Student» или «dem Studenten» оставалось непонятно.

`morph.import_dump()` заливает полные парадигмы из дампа немецкого Wiktionary.
Это **join, а не обогащение** — ни одного вызова Mistral. Замер на живой базе:
**48 403 из 76 332 карточек (63.4 %) за 75 s**, 36 428 существительных,
7 852 глагола, 4 123 прилагательных.

| | что кладём |
|---|---|
| verb | `praesens` (6 лиц), `praeteritum`, `partizip2`, `hilfsverb`, `imperativ_du/ihr`, `konjunktiv2` |
| noun | `sg`/`pl` × `nom/gen/dat/akk` |
| adj | `komparativ`, `superlativ` |

- Дамп — **немецкое издание**, не английское: 153 706 пригодных лемм против
  78 692, наших карточек находит 53 222 против 39 038, и формы приходят
  с местоимениями (`du gibst`), а не голыми. Весит втрое меньше (300 МБ).
  `https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz`
- Импорт **офлайновый** (`backend/scripts/import_morphology.py`) — дампу не место
  в образе. Ключ `(lemma, pos)`, регистр НЕ фолдится (Morgen ≠ morgen).
- **Гонять заново после КАЖДОГО вливания слов.** Парадигмы не доезжают до новых
  карточек сами: после интейка 19-го июля их было 0 из 15 725. Повторный проход
  дал **95 % на новых** (они сами из Wiktionary, поэтому находятся лучше старой
  базы с её 63 %), итого 48 403 → 63 340 (68.8 %) за 24 s.
- ⚠️ **Запускать только с явным `--enrich-db`.** Без него путь резолвится в
  пустышки `app/vocab/*.db` — та же ловушка, что описана для `intake.py` в §6a,
  но защиты у этого скрипта пока НЕТ. Признак подмены — `cards with a paradigm:
  0 of 0`: ноль в ЗНАМЕНАТЕЛЕ, а не в числителе. Схему в пустышке он при этом
  молча создаёт и рапортует успех.
- Зеркало тянет парадигму `LEFT JOIN`'ом на строке карточки, поэтому импорт
  публикуется тем же `full_resync`, что и правки zipf/form_kind на месте.
- Отбрасываются формы с `obsolete`/`archaic`/`variant`/региональными тегами.
  Голая степень сравнения отличается от склонённых ячеек по ЧИСЛУ тегов:
  у «besser» это `(comparative,)`, у «besserer» ещё падеж, род, число и сила.

> ⚠️ **`form_of` из Wiktionary НЕЛЬЗЯ использовать для опускания карточек.**
> Он зовёт не-леммами 6 533 наших карточки, включая `das`, `es`, `ein`, `aber`,
> `was`, `werden`, `schon`, `mehr`, `mal` — у каждого есть редкий омографичный
> разбор (`aber`→`abern`, `schon`→`schonen`, `mehr`→`mehren`). Даже строгий
> вариант «все значения формные» (2 209) забирает `alles`, `andere`, `weniger`,
> `nächste`, `Gute`, `Ganze`. Для ранжирования работает только сигнал самого
> словаря — см. выше про `forms.py`. Wiktionary даёт морфологию, но не право
> судить, что слово, а что нет.
### Админ-флот (2026-07-17)

Одна кнопка поднимает воркер на КАЖДОМ аккаунте с привязанным ключом — раньше это
означало 10 вкладок, по одной на аккаунт. Проверено вживую: 15 из 17 стартовали,
два ключа Mistral отвечают 401 и панель их называет.

- Права — **только `ADMIN_EMAILS` в `backend/.env`**, ручки выдачи нет и быть не
  должно: админ тратит ЧУЖИЕ ключи. Пусто (дефолт) → админов нет.
  `is_admin` в `/api/auth/me` решает лишь, рисовать ли панель; каждый роут
  перепроверяет права сам. Смена переменной требует рестарта, а рестарт убивает
  живые воркеры — см. верх файла.
- **Один плохой аккаунт не стоит остальным ночи**: расшифровка ключа и старт идут
  по-аккаунтно, ошибка становится строкой в `failed`, а не 500 на весь вызов.
  Реальный случай — ключ, зашифрованный под старым `MISTRAL_KEY_SECRET`.
- **Токены**: `enrichment.db.token_usage` (user_id, UTC-день). Считаются из блока
  `usage` ответа Mistral — `post_mistral_json(on_usage=…)`, до этого envelope
  выбрасывался целиком. Лежат в SQLite, а не в Postgres, потому что воркер —
  синхронный поток, который уже владеет этим файлом; ради счётчика заводить
  event loop на воркер незачем. Учёт **никогда не роняет батч**: карточки уже
  оплачены, поэтому ошибка записи логируется и глотается.
  Порог НЕ останавливает работу — решение владельца: показывать расход, не резать.
- Панель на `pipeline.html` (`#adminCard`), опрос — общий `refreshProgress` (2.5s).
  В **фоновой вкладке Chrome throttl'ит `setInterval` до ~1/мин** — это не баг,
  цифры догоняют при возврате фокуса.

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
- Курсор умеет только ДОБАВЛЯТЬ, поэтому есть `mirror.prune_orphans()`: карточку
  можно и удалить (skip на повторном проходе, переименование орфографии), и без
  этого зеркало вечно отдавало бы ровно то, что мы только что забраковали.
  Прунер **отказывается работать, если источник прочитался пустым** — иначе
  «удалить всё, чего нет в пустом множестве» снесёт словарь. Устаревшее зеркало
  чинится, пустое — это авария.
- `mirror.sync_cards(since=(0.0,""))` — полный проигрыш вместо курсора. Нужен,
  когда колонку добили на месте (`created_at` не двигается → курсор её не увидит).

### Поиск

- Раскладка решает язык: латиница → немецкая лемма, кириллица → `ru_all`.
- **Две нормализованные колонки** на немецкой стороне: `lemma_norm` (grün→gruen)
  и `lemma_ascii` (grün→grun). Обе индексируются GIN/trigram и обе всегда
  участвуют в запросе. Одной мало: у запроса «grun» умляутов нет, обе его свёртки
  совпадают — но само слово хранится по-разному, и без `lemma_ascii` «grün»
  не находится вовсе (проверено: выше него встают Grund и Grunzen).
- **Ранжирование: `score DESC, form_kind IS NULL DESC, zipf DESC NULLS LAST,
  length, регистр, lemma`.** Частота обязана стоять выше длины. У всех точных
  совпадений «быстрый» одинаковый score 2.0, тайбрейк уходил на
  `length(lemma_norm)` — и `schnell` (zipf 5.51, 354-е слово немецкого)
  оказывался ПОСЛЕДНИМ, после fix/rasch/prompt/rapide/zügig. `zipf` лежал в
  `vocab.db` для всех 108k слов и просто не доезжал до зеркала.
- **Регистр запроса — последний тайбрейк, и он единственный, кто разводит пары
  вида `Die`/`die`.** `wordfreq` фолдит регистр, поэтому такая пара не просто
  близка по частоте — у неё **побайтово одинаковый zipf**: замерено на всех 275
  парах с zipf ≥ 4.0, совпадают ВСЕ без исключения. Дальше тайбрейк падал на
  `lemma`, где `'D' < 'd'`, заглавная побеждала всегда, и самое частотное слово
  немецкого языка отвечало `Die` «чип». Так же `Aber` «возражение» над `aber`,
  `Aus` «аут» над `aus`, `Gut` «имущество» над `gut`.
  ⚠️ Эти заглавные — **не мусор**: `das Aber` и `das Gut` настоящие
  субстантивации, и `forms.py` намеренно выводит их из-под тега `capitalised`
  (проверка на артикль). Врёт только унаследованная частота, поэтому карточку
  **опускают, а не удаляют** — обе остаются в выдаче соседними строками.
  ⚠️ Признака, который отличал бы редкую субстантивацию (`das Jetzt`) от частой
  (`der Morgen`), в данных НЕТ — это пословная частотность значения, которой у
  нас нет. Зато есть регистр, который набрал пользователь, и он прямо выражает
  намерение: «Morgen» просит существительное, «morgen» — наречие. Строчный или
  кириллический запрос откатывается на «сначала строчное». Любая попытка
  «нормализовать» регистр запроса до `_by_relevance` возвращает баг.
- Русская морфология вытягивается триграммами без стеммера
  (`зависимостью`→`зависимость` = 0.79 при пороге 0.3).
- Ничего не нашли → так и говорим. База ещё обогащается, выдавать вместо ответа
  случайные близкие слова — хуже честного «нет».

### Ключ личного списка

`user_word_list` адресует слово **строкой `lemma`**, без FK на `vocab_cards`:
промпт обогащения разводит омографы регистром (Morgen/morgen, Essen/essen),
а будущее расширение будет слать слова с произвольных страниц, которых в базе
может не быть.

> ⚠️ До 2026-07-17 это утверждение было верно только про ПРОМПТ. Модель отвечала
> правильно, а `parse_response` фолдил регистр при сопоставлении и выбрасывал одну
> из двух карточек — см. §6a. Регистр в `lemma` несёт смысл; любой код, который
> «нормализует» лемму перед поиском соответствия, ломает омографы. Колонки-снимок (`ru`, `band`, `pos`, …) нужны, чтобы список
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
Фаза 8  ✅ Качество базы (2026-07-17): фазы починки за одной кнопкой, точное
           сопоставление регистра, орфография 1996, zipf в ранжировании — §6a/§6b
```

### Что осознанно НЕ делаем (проверено 2026-07-17)

**Массовый requeue по «подозрительной» частоте.** Гипотеза была: `unlisted` +
высокий zipf = словоформа, которой выдумали редкое значение (`einen`→объединять,
`hast`→спешка, `Stunden`→отсрочивать). Проверка не подтвердила её как фильтр:
в зоне zipf 4.5–4.8 сидят нормальные `Funktion`, `Anteil`, `Armee`, `Konzept`, а
даже при zipf ≥ 5.0 половина легитимна (`Würde`=достоинство, `Macht`=власть,
`Art`=вид, `Prozent`, субстантивированные `Alte`/`Ganze`). Из 94 карточек
zipf ≥ 5.0 двадцать уже чинятся как омографы, а явного брака остаётся ~15.
Слепой requeue сломал бы хорошие карточки ради пятнадцати. Вместо ретро-починки
правило про Wortform добавлено В ПРОМПТ — чтобы брак не создавался на оставшихся
17k, а не чтобы рискованно переписывать уже готовое.

**`confidence` как сигнал.** `high` — 64 455, `low` — 18. Модель всегда пишет
`high`, так что `requeue_low_confidence` найдёт 18 слов из 64 тысяч. Ручка живая,
но опираться на неё как на поиск плохих карточек нельзя.

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
