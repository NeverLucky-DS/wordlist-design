# Wörterbuch — UI kit

The thematic dictionary screen. A multi-column list of **watercolor word rows**
(each painted by CEFR level × grammatical type), a page search, category filter
chips, and a fixed right rail with the level-distribution donut and the standing
Wittgenstein quotation. Click any word: the list reflows to a single column and
a premium **detail sheet** opens on the right (meaning, pull-quote, grammar spec
strip, Verwendung panel, numbered bilingual examples).

**Files**
- `index.html` — page shell + fixed furniture CSS (watercolor column, side
  label, right rail), mounts the app.
- `Woerterbuch.jsx` — the interactive screen. Composes `TopBar`, `SearchField`,
  `Chip`, `WordRow`, `LevelTag` from the bundle; adds the donut and detail sheet.

**Composes:** TopBar · SearchField · Chip · WordRow · LevelTag.

Brush assets are referenced via `brushBase="../../assets/brushes/"`.
