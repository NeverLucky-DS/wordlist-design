# Промпты на графику для Wörterbuch

Пять брифов, **15 файлов**. Ни один не декоративен «просто так»: у каждого
описано, что он делает и чем страница хуже без него. Все слоты уже нарисованы
пунктиром прямо в макете — снимите галочку «слоты под графику» внизу страницы,
чтобы увидеть, как всё выглядит, если графика не приедет вовсе.

---

## Общие требования — обязательны для ВСЕХ 15 файлов

Скопируйте этот абзац в конец каждого промпта:

> Transparent background (alpha channel), PNG-24 with true 8-bit alpha, sRGB.
> No white background, no off-white background, no paper texture, no canvas
> grain, no scanned-paper look. No drop shadow, no glow, no outline, no border,
> no frame, no vignette. No text, no letters, no numbers, no signature, no
> watermark. No hard geometric edges — every edge is soft watercolour bleed
> fading to full transparency. Flat 2D, no 3D, no perspective, no photographic
> lighting. Single continuous wash, not a collage of strokes.

### Технические параметры

| Параметр | Значение | Почему именно так |
|---|---|---|
| Формат | **PNG-24 + alpha** | Всё это — полупрозрачные подложки и CSS-маски |
| Цветовое пространство | sRGB, без встроенного ICC | Иначе оттенок поедет между Chrome и Safari |
| Разрешение файла | **×2 от CSS-размера** (в таблицах ниже) | Retina |
| Фон | **полностью прозрачный**, alpha = 0 | Не белый и не «почти белый» |
| Края | мягкие, alpha уходит в 0 плавно | Жёсткий край мгновенно читается как коробка |
| Оптимизация | `oxipng -o4 --strip safe` (lossless) | |

> ⛔️ **Lossy WebP запрещён.** Это правило владельца проекта, записанное в
> `info/CRITICAL-LINKS.md` §4: на альфа-канале lossy WebP даёт ореолы, грязные
> края и ломает CSS `mask`. Только PNG lossless или lossless WebP со
> сравнением глазами.

### Проверка перед коммитом

```bash
# 1. альфа на месте и фон действительно прозрачный
python3 -c "
from PIL import Image; import sys
for f in sys.argv[1:]:
    im = Image.open(f).convert('RGBA'); a = im.getchannel('A')
    print(f, im.size, 'mode', Image.open(f).mode,
          'угловая alpha', a.getpixel((0,0)),
          'мин/макс alpha', a.getextrema())
" images/card/*.png worte/row/*.png
# угловая alpha обязана быть 0; getextrema обязан начинаться с 0

# 2. lossless-оптимизация
oxipng -o4 --strip safe images/card/*.png worte/row/*.png
```

---

## A. Шапка карточки — `card-head-*.png` (5 файлов)

**Куда:** `images/card/`  ·  **CSS-размер** 440 × 152  ·  **файл 880 × 304**

### Зачем

Сейчас шапка берёт мазок **строки списка** — широкий горизонтальный штрих,
нарисованный под строку в 700 px, — и растягивает его на блок 440 × 152.
В V9 он шёл на `opacity:.5` под белой вуалью, доходящей до `.93`, то есть
краска превращалась в еле заметное пятно, и цветовое кодирование пропадало.
На `berücksichtigen` штрих ложился ровно поперёк леммы и IPA и читался как
зачёркивание. Нужна краска, нарисованная **под эту форму и этот размер**.

### Почему пять файлов, а не пятнадцать

Существующие 15 мазков закодированы ключом `band|type`. Но `band` — **заглушка
у 95.6 % карточек** (88 067 из 92 090 — `unlisted`, потому что Goethe публикует
списки только A1/A2/B1). То есть половина того, что кодирует мазок строки, —
догадка. **Новый ассет не должен тиражировать догадку**, поэтому шапка
кодируется только по `type`, который настоящий у каждой карточки. Уровень и так
написан текстом в той же строке меты. Существующие 15 мазков строк не трогаются.

### Промпт (подставить цвет и имя)

```
A soft watercolour wash band for the top of a dictionary card. Horizontal
landscape format, 880 x 304 pixels.

The paint occupies the UPPER TWO THIRDS of the frame and dissolves completely
before it reaches the bottom edge, so the lower third is clean transparency —
text will be set there and must sit on empty ground.

Density: strongest in the upper-left quadrant, thinning as it travels right,
with one or two paler pooled areas where the pigment settled and dried with a
slightly darker rim, the way real watercolour blooms on wet paper. One or two
faint pigment granulations. The right edge feathers out and never reaches the
frame edge.

Colour: a single hue — <ЦВЕТ> — in a light, dusty, faded register. Muted and
desaturated, like a wash left in a sketchbook for twenty years. Opacity of the
densest area about 55–65%; most of the wash is far lighter than that.

Transparent background (alpha channel), PNG-24 with true 8-bit alpha, sRGB.
No white background, no off-white background, no paper texture, no canvas
grain, no scanned-paper look. No drop shadow, no glow, no outline, no border,
no frame, no vignette. No text, no letters, no numbers, no signature, no
watermark. No hard geometric edges — every edge is soft watercolour bleed
fading to full transparency. Flat 2D, no 3D, no perspective, no photographic
lighting. Single continuous wash, not a collage of strokes.
```

### Пять цветов

| Файл | `<ЦВЕТ>` в промпте | Опорный hex | Откуда |
|---|---|---|---|
| `card-head-der.png` | `dusty powder blue` | `#9DB2C9` | семейство der (Powdery-Blue → Indigo) |
| `card-head-die.png` | `dusty rose pink` | `#C2868D` | семейство die (Powdery-Pink → Burgundy) |
| `card-head-das.png` | `faded sage green` | `#9DBFA4` | семейство das (Pale-Green → Emerald) |
| `card-head-verb.png` | `warm sandy ochre` | `#CDB68F` | семейство verb (Sandy-Ochre → Olive) |
| `card-head-adj.png` | `muted lavender` | `#A99BC0` | семейство adj (Lavender → Plum) |

### Как подключается

```css
.wb-head::before{background:url('../images/card/card-head-die.png') no-repeat top center/100% auto;
                 opacity:1}          /* прозрачность уже в самом файле */
```
Вуаль `.wb-head::after` после этого **ослабляется до .18/.55/.80** — она была
компенсацией за то, что краска ложилась на текст; у нарисованной под форму
шапки текст и так стоит на чистом.

**Приёмка:** положить файл под лемму `berücksichtigen` (самое длинное слово,
кегль 32) и под `Herz` (кегль 50). Ни одна буква и ни один знак IPA не должны
пересекаться с плотной частью краски.

---

## B. Шкала частотности — `freq-*.png` (3 файла)

**Куда:** `images/card/`  ·  **CSS-размер** 58 × 14 (в карточке), 44 × 11 (в строке)
·  **файл 116 × 28**

### Зачем

Сейчас частотность — фраза, которую надо прочитать («средней частоты»). Шкала
читается мгновенно. И, в отличие от цифры или буквы, она **физически не может
быть принята за уровень CEFR** — а именно этого мы избегаем намеренно: на
4 023 карточках с настоящей разметкой Goethe частотность не отличает B1 от B2
вообще (медианы 4.16 и 4.15). Рисуется только там, где частота известна:
пустая шкала означала бы «редкое», а это утверждение, которого у нас нет.

### Промпт

```
Three tiny hand-painted watercolour tally marks in a row, like ink strokes in
a field notebook. Format 116 x 28 pixels, horizontal.

Each mark is a short vertical dash about 14 pixels wide and 22 pixels tall,
evenly spaced across the frame, hand-drawn and slightly irregular — not
identical, not machine-straight, each with a soft blotted end.

<СОСТОЯНИЕ>

Colour: warm graphite-plum, hex #8C4F57, in a watercolour register.
The filled marks sit at about 85% opacity; the empty marks are only the faint
ghost of a stroke, about 20% opacity.

Transparent background (alpha channel), PNG-24 with true 8-bit alpha, sRGB.
No white background, no off-white background, no paper texture, no canvas
grain, no scanned-paper look. No drop shadow, no glow, no outline, no border,
no frame, no vignette. No text, no letters, no numbers, no signature, no
watermark. No hard geometric edges — every edge is soft watercolour bleed
fading to full transparency. Flat 2D, no 3D, no perspective, no photographic
lighting. Single continuous wash, not a collage of strokes.
```

| Файл | `<СОСТОЯНИЕ>` |
|---|---|
| `freq-haeufig.png` | `All three marks are fully painted and saturated.` |
| `freq-mittel.png` | `The first two marks are fully painted; the third is a faint ghost.` |
| `freq-selten.png` | `Only the first mark is painted; the second and third are faint ghosts.` |

**Приёмка:** уменьшить до 44 × 11 и посмотреть с расстояния вытянутой руки.
Три состояния обязаны различаться **без чтения подписи**. Если различаются
только вблизи — просить увеличить контраст между 85 % и 20 %.

---

## C. Мазок строки списка — `row-brush-*.png` (5 файлов)

**Куда:** `worte/row/`  ·  **CSS-размер** переменный, высота 58  ·  **файл 560 × 160**

### Зачем

Это прямой ответ на «мазки выглядят как чиркаши на туалетной бумаге».
Сегодняшние ассеты нарисованы как **широкие горизонтальные штрихи**, а CSS
задаёт им `width:108%; height:165%` **от строки** — в колонке 744 px
компактное пятно растягивается в ~800 × 105.

В прототипе мазок уже повешен на само слово и растягиваться не может, но
исходники всё ещё вытянутые: чтобы влезть в короткую метку под `online`, их
приходится кадрировать `cover`, и от рисунка остаётся середина. Нужны
исходники, нарисованные **как компактное пятно**, которое переживает и сжатие
под короткое слово, и растяжение под длинное.

### Почему снова пять, а не пятнадцать

Та же причина, что у шапки: `band` — заглушка у 95.6 % карточек. Уровень
показан бейджем текстом. Пятнадцать существующих файлов остаются на месте и
никуда не деваются — новые пять кладутся рядом, в подпапку, и подключаются
только если владелец решит перевести строку на кодирование по части речи.

### Промпт (подставить цвет и имя)

```
A single compact watercolour brush mark, painted in one confident horizontal
stroke. Format 560 x 160 pixels.

The stroke is a soft elongated pool of pigment centred in the frame, about
three times wider than it is tall. Density is greatest slightly left of centre
and thins toward BOTH ends, where the paint breaks into dry-brush and fades
completely before reaching the left and right frame edges. Top and bottom
edges are irregular and soft — the mark is the shape a loaded flat brush
leaves on damp paper, not a rectangle.

One or two pale blooms inside the pool where the water pushed pigment outward
and left a slightly darker settling rim. Faint granulation. Nothing crosses
the frame boundary anywhere.

Colour: a single hue — <ЦВЕТ> — light, dusty and desaturated. Densest area at
about 50% opacity, most of the mark much lighter. Text will be set on top of
this mark and must stay readable, so the whole wash is pale.

Transparent background (alpha channel), PNG-24 with true 8-bit alpha, sRGB.
No white background, no off-white background, no paper texture, no canvas
grain, no scanned-paper look. No drop shadow, no glow, no outline, no border,
no frame, no vignette. No text, no letters, no numbers, no signature, no
watermark. No hard geometric edges — every edge is soft watercolour bleed
fading to full transparency. Flat 2D, no 3D, no perspective, no photographic
lighting. Single continuous wash, not a collage of strokes.
```

Цвета — те же пять, что в брифе A (`der` голубой, `die` розовый, `das`
зелёный, `verb` охра, `adj` лавандовый). Имена файлов:
`row-brush-der.png`, `row-brush-die.png`, `row-brush-das.png`,
`row-brush-verb.png`, `row-brush-adj.png`.

**Приёмка — самая важная из всех.** Положить один и тот же файл под `online`
(85 px слова) и под `die Verantwortung` (230 px) в варианте A. Ни там, ни там
он не должен читаться как «чиркаш»: под коротким словом это компактное пятно,
под длинным — длинный мазок, но в обоих случаях **пятно, а не полоса**. Если
под длинным словом рисунок размазывается — просить более выраженную середину.

---

## D. Тушевая линейка — `rule-ink.png` (1 файл)

**Куда:** `images/card/`  ·  **CSS-размер** 388 × 5, тайлится  ·  **файл 1200 × 12**

### Зачем

Между блоками карточки сейчас `border-top: 1.5px solid var(--hair)` — идеально
ровная машинная линия. Это единственное место, где карточка выдаёт, что она
CSS-коробка, а не лист. Один файл на всю карточку, эффект несоразмерно
больший, чем стоимость.

### Промпт

```
A single horizontal hairline drawn by hand with a fine ink brush.
Format 1200 x 12 pixels, extremely thin.

The line runs the full width of the frame and touches both the left and right
edges cleanly at the same vertical position and the same weight, so that
copies of the image placed side by side join into one continuous unbroken
line with no visible seam.

Along its length the line varies naturally: slightly thicker where the brush
pressed, thinner and almost breaking in one or two places, with a faint
feathering at the underside. It is not perfectly straight — it wanders by one
or two pixels — but it never bends far enough to look wavy.

Colour: warm grey-taupe, hex #C9C3BA, at about 70% opacity.

Transparent background (alpha channel), PNG-24 with true 8-bit alpha, sRGB.
No white background, no off-white background, no paper texture, no canvas
grain, no scanned-paper look. No drop shadow, no glow, no outline, no border,
no frame, no vignette. No text, no letters, no numbers, no signature, no
watermark. No hard geometric edges. Flat 2D, no 3D, no perspective, no
photographic lighting.
```

**Подключение:** переменная `--rule-ink` уже заведена в `wb.css` — блок
`.wb-blk+.wb-blk` рисует её как фон и гасит собственную границу классом
`has-rule`. Если файла нет, остаётся CSS-граница, то есть разделитель не
пропадает никогда.

**Приёмка:** поставить две копии встык и посмотреть на стык при зуме 400 %.
Шва быть не должно.

---

## E. Штрих активной вкладки — `tab-stroke.png` (1 файл)

**Куда:** `images/card/`  ·  **CSS-размер** 120 × 5  ·  **файл 240 × 10**

### Зачем

Активную вкладку сейчас отмечает прямоугольник со скруглением. В навигации
сайта та же роль уже отдана акварельному подчёркиванию
(`images/header/nav-active-stroke.png`), и вкладки карточки — единственное
место, где та же рифма не звучит. Существующий файл не переиспользуется: он
2 МБ и нарисован под ширину пункта меню.

### Промпт

```
A single short horizontal brush underline, as if drawn with one quick pass of
a loaded flat brush. Format 240 x 10 pixels.

The stroke sits centred and spans about 90% of the frame width, fading to
nothing at both ends. It is thickest in the middle third and tapers toward the
tips; the lower edge is slightly ragged where the brush lifted, the upper edge
is cleaner.

Colour: dusty rose, hex #C2868D, at full saturation for this palette — this
mark is a state indicator and must read clearly, so it is the most saturated
of the five briefs.

Transparent background (alpha channel), PNG-24 with true 8-bit alpha, sRGB.
No white background, no off-white background, no paper texture, no canvas
grain, no scanned-paper look. No drop shadow, no glow, no outline, no border,
no frame, no vignette. No text, no letters, no numbers, no signature, no
watermark. No hard geometric edges — every edge is soft watercolour bleed
fading to full transparency. Flat 2D, no 3D, no perspective, no photographic
lighting.
```

**Подключение:** используется **как маска**, а не как картинка, — тогда цвет
задаётся из CSS и его можно менять, не перерисовывая файл:

```css
.wb-tab.on::after{--tab-stroke:var(--rose);
  --tab-stroke-mask:url('../images/card/tab-stroke.png') no-repeat center/100% 100%}
```
Поэтому в файле важна **форма альфа-канала**, а цвет — только ориентир.

---

## Сводка

| Бриф | Файлов | Размер файла | Куда кладётся | Без него |
|---|---|---|---|---|
| A. шапка карточки | 5 | 880 × 304 | `images/card/` | шапка белая, кодировки по роду нет |
| B. шкала частотности | 3 | 116 × 28 | `images/card/` | частотность только словами |
| C. мазок строки | 5 | 560 × 160 | `worte/row/` | остаются растянутые исходники |
| D. тушевая линейка | 1 | 1200 × 12 | `images/card/` | ровная CSS-граница |
| E. штрих вкладки | 1 | 240 × 10 | `images/card/` | скруглённый прямоугольник |
| **итого** | **15** | | | |

Порядок ценности, если делать не всё сразу: **C → A → D → B → E.**
C чинит названную вслух претензию, A — самая заметная поверхность, D стоит
один файл, B и E — приятная отделка.

**После добавления файлов** — дописать пути в `info/CRITICAL-LINKS.md` §3
(таблица ссылок на изображения) и в `docker-compose.yml`, если появляется
новый корневой каталог (§7 п. 3).
