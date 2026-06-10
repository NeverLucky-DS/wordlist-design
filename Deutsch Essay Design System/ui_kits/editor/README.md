# Editor (Schreiben) — UI kit

The distraction-free writing surface. A three-column grid: the **essay map**
(numbered sections on a vertical track + writing-goal progress + niveau), the
**writing surface** (meta selects, serif title, an editable Cormorant document,
the "Analysieren" CTA, autosave foot), and **three calm tools** — a
lilac-watercolor Pomodoro timer, a Klischees (sentence-starter) panel with a
pager, and an inline Wörterbuch with compact watercolor rows.

**Files**
- `index.html` — page shell + the editor layout CSS (grid, essay map, writing
  card, tool rails), mounts the app.
- `Editor.jsx` — the interactive screen. Composes `TopBar`, `Button`,
  `IconButton`, `Select`, `ProgressBar`, `ToolCard`, `SearchField`, and the
  `WASH` brush map from the bundle; types update the live word count + progress.

**Composes:** TopBar · Button · IconButton · Select · ProgressBar · ToolCard ·
SearchField · (WASH brush map).

Imagery referenced: `../../assets/images/abstract-watercolor-column.png` (Pomodoro wash),
`../../assets/brushes/` (compact dictionary rows).
