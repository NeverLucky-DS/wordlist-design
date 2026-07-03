# Deutsch Essay — Design System

A premium, editorial design system for **Deutsch Essay**, an AI-assisted German
essay trainer for CEFR levels B1–C1. The product pairs a thematic dictionary
(*Wörterbuch*), a distraction-free writing surface (*Schreiben / Editor*) with
streaming AI analysis, and a word-enrichment pipeline. The whole thing feels
like *expensive paper* — warm ivory, a literary serif, and a single disciplined
muted-plum accent — with one signature flourish: **watercolor brush strokes**
that paint every dictionary word according to its CEFR level and grammatical
type.

> **Direction in one line:** premium digital stationery — ivory paper, graphite
> ink, faded watercolor, and exactly one live accent.

---

## Sources

This system was reverse-engineered from the product's real front-end code and
screenshots. Explore these to build more faithfully:

- **GitHub — Deutsch Essay Trainer (`wordlist-design`):**
  https://github.com/NeverLucky-DS/wordlist-design
  - `css/styles.css` — the Wörterbuch (dictionary) styling & watercolor washes
  - `css/editor.css` — the Editor (Schreiben) styling, autumn accent, tools
  - `css/site-header.css` — the shared top bar (1:1 across pages)
  - `js/app.js` — the dictionary data model, brush map (`WASH`), word cards
  - `images/`, `worte/` — watercolor columns, decor marks, and the 15 brush PNGs
  - `screenshots/` — reference renders of every surface
- Related repos by the same author (context, not used here): `Deutsch`,
  `German` (private), `Closed_hub`.

The brand uses two real Google Fonts — **Cormorant Garamond** (serif) and
**Inter** (sans). No substitutions were needed.

---

## Content fundamentals

**Languages.** The interface is **German** (DE). Word glosses, AI explanations,
and clichés carry a **Russian** translation alongside — the product is built for
Russian-speaking learners of German. UI chrome stays German; helper text and
explanations are Russian.

**Voice & address.** Calm, literary, encouraging — a patient tutor, never a
gamified app. German UI uses the **formal "Sie"** ("Wählen Sie ein Wort…",
"Ihr thematischer Wortschatz"). Copy is concise and declarative.

**Casing.** German nouns are capitalised (as the language requires). UI labels
and eyebrows are **UPPERCASE with wide tracking** ("WÖRTERBUCH", "BEDEUTUNG",
"VERTEILUNG NACH NIVEAU"). Section labels are centred and flanked by hairlines.

**Tone examples (verbatim from the product):**
- Lede: *"Ihr thematischer Wortschatz für präzises Deutsch. Wählen Sie ein Wort,
  um Bedeutung, Grammatik und Beispiele zu sehen."*
- Eyebrow → title pattern: *TECHNOLOGIE* → *Argument Eins* → *"Das stärkste
  Argument zuerst"*.
- A standing quotation anchors the dictionary rail: *"Die Grenzen meiner Sprache
  bedeuten die Grenzen meiner Welt." — Wittgenstein.*
- AI notes are structured in Russian: *ЧТО НЕ ТАК* (what's wrong) · *ПОЧЕМУ
  ВАЖНО* (why it matters) · *ВАРИАНТЫ* (variants, labelled B1/B2).

**No emoji.** None anywhere in the product. Tone is set by the serif, the paper,
and the paint — never by emoji or playful iconography. A single ★ glyph appears
inside the "Analysieren" CTA; otherwise iconography is line-SVG.

**Numerals** are set in the serif (Cormorant) for display (word counts, the
Pomodoro clock, niveau letters), tabular sans for dense UI counts.

---

## Visual foundations

**Colour.** The world is warm ivory paper (`--bg #FAF8F4`) with warm graphite
ink (`--ink #2A2420`, never pure black). There is **one live accent — soft
orchid** (`--accent #6C6580` → `--accent-2 #8A8299`), used only for interactive
or "now" states (the primary CTA, the active nav underline, the caret, the live
connector). Discipline is the point: because colour is rare, it means something.
A **separate faded-watercolor palette** — rose `#C2868D`, blue `#9DB2C9`,
lavender `#A99BC0` — encodes CEFR level (B1 · B2 · C1) and appears **only as
paint** (brush washes, the distribution donut, the header level pill), never as
a flat UI fill.

**Type.** Two voices that rarely meet at the same size. **Cormorant Garamond**
(serif) is the *content*: the display titles (76px), every German word (26px in
a row, up to 54px in a card), the writing surface itself (21px / 1.85), and
italic translations & pull-quotes. **Inter** (sans) is the *chrome*: small,
calm, uppercase-tracked labels, nav, meta, counts, and Russian glosses. The
serif goes big; the sans stays small.

**Backgrounds & texture.** The page is flat warm ivory, lifted by a very faint
two-point radial grain (warm). The signature decoration is a **real watercolor
column PNG** bleeding off the left edge, masked so it melts into the page before
it reaches the content. The Editor adds a slim echo of the same column in its
gutter. There are **no gradients as backgrounds** (the only gradients are the
muted-plum CTA fill, the nav underline, and the progress fill). Imagery is
soft, painterly — lilac & rose watercolor washes, abstract paint, botanical marks —
always quieted under a heavy white scrim when it sits behind text.

**The brush system (the heart).** Each dictionary word is painted with its own
brush PNG, keyed by **level × grammatical type** (der/die/das/Verb/Adjektiv) —
15 strokes total. The stroke is shown only on its **left** portion (a soft 3-step
organic mask); on hover or when the word is opened, the *hidden continuation*
is **"drawn in" to the right** on a springy ease (`--ease-spring`) — the paint
never moves or scales, it only reveals. Opacity rises from ~.6 to ~.92. Black
text rides over the densest paint with a faint white halo for legibility.

**Animation.** Gentle, with a touch of inertia. Default UI ease is
`cubic-bezier(.2,.8,.2,1)`; the brush draw-in uses a slightly springy
`cubic-bezier(.34,1.12,.36,1)` over ~460ms. The live connector is a dashed
orange Bézier with marching-ants (`stroke-dashoffset` loop). Durations: 160ms
(press), 220ms (hover/colour), 460ms (brush). No bounces on content, no infinite
decorative loops except the connector's ants. Reduced-motion disables them.

**Hover / press.** Quiet cards lift (`translateY(-1…-2px)`) and gain a warm,
long shadow; borders warm from `--line` to `--accent-ln` (or `--rose` on the
Wörterbuch). The primary CTA lifts and deepens its glow on hover, settles to 0
on press. Chips grow slightly and darken to graphite when active. Icon buttons
warm their border + icon to accent.

**Borders, radii, shadows.** Hairlines are warm and pale (`--line #ECE7DE`).
Corners round softly: cards 18–22px, controls 11–14px, tags 8px, pills/avatars
full. Shadows are **warm and long** — light falling on paper, never a hard grey
drop; the premium "floating sheet" stacks four layers. The accent glow appears
**only** under live orange controls.

**Layout.** Wide, breathing gutters (up to 100px). Fixed left edge furniture:
the watercolor column, a vertical side-label (e.g. "WÖRTERBUCH"), and a "Niveau"
cap. A fixed right rail carries the level-distribution donut and the standing
quotation. The Editor is a three-column grid: essay-map · writing surface ·
three calm tools. The dictionary reflows from a multi-column list to a
single-column + detail-sheet when a word is opened, joined by the live orange
connector.

**Transparency & blur.** Used sparingly and purposefully: the top bar is frosted
ivory (`backdrop-filter: blur(14px) saturate(140%)`); popovers use a light
translucent paper with a small blur. Everything else is opaque paper.

---

## Iconography

- **System:** hand-picked **line SVGs**, ~2px stroke, round caps/joins, drawn
  inline in the markup (no icon font, no sprite, no PNG icons). Examples in the
  product: search (magnifier), chevron-down (nav/menus/pills), sun (theme),
  folder, plus (new essay), play/reset (Pomodoro), speaker (Aussprache), star
  (favourite), close (×), and the small ★ inside the "Analysieren" CTA.
- **Stroke & fill:** mostly stroked (`fill:none;stroke:currentColor`), so icons
  inherit text colour and warm to accent on hover. A few are filled (speaker,
  the CTA star).
- **No emoji, no Unicode pictographs** as icons. The ellipsis "…" and the chevron
  glyphs in pagers are the only character-based marks.
- **Substitution note:** the product ships its own inline SVGs, so this system
  reproduces them inline rather than pulling a library. If you need a broader
  icon set for a new surface, use **Lucide** (https://lucide.dev) — its 2px
  round-cap line style matches exactly. **Flag any Lucide use** as an addition
  beyond the source product.

Brand imagery lives in `assets/` — see the index below.

---

## Index — what's in this folder

**Foundations**
- `styles.css` — the entry point (consumers link this one file; `@import`s only).
- `tokens/colors.css` — surfaces, ink ramp, the accent, CEFR watercolor, aliases.
- `tokens/typography.css` — families, the serif/sans scales, weights, tracking.
- `tokens/spacing.css` — spacing scale, radii, shadows, motion, z-index.
- `tokens/fonts.css` — Cormorant Garamond + Inter (Google Fonts).

**Specimen cards** (Design System tab) — in `guidelines/`
- Type: `type-display`, `type-body`, `type-labels`, `type-reading`
- Colors: `colors-surfaces`, `colors-ink`, `colors-accent`, `colors-levels`
- Spacing: `spacing-scale`, `radii`, `shadows`
- Brand: `brand-brushes`, `brand-brush-palette`, `brand-decor`, `brand-connector`

**Components** (`components/<group>/`) — React primitives, each with `.jsx`,
`.d.ts`, `.prompt.md`, and a group card:
- `buttons/` — **Button**, **IconButton**
- `forms/` — **SearchField**, **Select**
- `display/` — **Card**, **LevelTag**, **Avatar**, **Eyebrow**
- `navigation/` — **Chip**, **TopBar**
- `word/` — **WordRow** *(the signature watercolor entry)*
- `tools/` — **ToolCard**, **ProgressBar**

Use components in card/kit HTML via the compiled bundle:
`const { Button, WordRow } = window.DeutschEssayDesignSystem_3bc91c` after
`<script src="…/_ds_bundle.js">`.

**UI kits** (`ui_kits/<product>/`)
- `woerterbuch/` — the thematic dictionary (list, watercolor rows, detail sheet)
- `editor/` — the writing surface (essay map, document, three tools, AI note)

**Assets** (`assets/`)
- `assets/brushes/` — the 15 watercolor brush PNGs (level × type)
- `assets/images/` — watercolor column, lilac wash (Pomodoro), paper texture, decor
  marks, botanical, Verwendung/Deklination panels

**`SKILL.md`** — makes this folder usable as a downloadable Claude Agent Skill.

---

## Using this system

1. Link `styles.css`. Build on the tokens — never invent new colours; if you
   must, derive in OKLCH from the existing palette.
2. Reach for the serif for anything that is *content*; keep the sans small and
   for *chrome*.
3. Spend the accent sparingly. One primary action per view.
4. When you show vocabulary, use **WordRow** — the watercolor is the brand.
5. Keep it paper: warm ivory, warm shadows, hairline borders, soft rounding.
