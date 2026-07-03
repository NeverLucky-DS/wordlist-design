---
name: deutsch-essay-design
description: Use this skill to generate well-branded interfaces and assets for Deutsch Essay (an AI-assisted German B1–C1 essay trainer), either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, the signature watercolor brush system, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the `readme.md` file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Quick orientation

- **Foundations:** link `styles.css` (it `@import`s `tokens/*.css`). Everything
  is a CSS custom property — surfaces, the warm ink ramp, the one muted-plum
  accent, the CEFR watercolor palette, type scales, spacing, radii, shadows.
- **The look:** warm ivory paper, graphite ink, Cormorant Garamond (serif,
  content) + Inter (sans, chrome), one disciplined orange accent, and the
  signature **watercolor brush** painting every dictionary word by level × type.
- **Components** live in `components/<group>/` as React primitives — Button,
  IconButton, SearchField, Select, Card, LevelTag, Avatar, Eyebrow, Chip,
  TopBar, **WordRow** (the signature), ToolCard, ProgressBar.
- **UI kits** in `ui_kits/` recreate the real product screens (Wörterbuch,
  Editor) — read them to see how primitives compose into full views.
- **Assets** in `assets/brushes/` (15 watercolor strokes) and `assets/images/`
  (watercolor column, lilac wash, paper, decor marks, panels).

## Rules of thumb

1. Serif for content (titles, German words, the writing surface, italic
   translations). Sans, small, for chrome (labels, nav, meta, glosses).
2. One primary action per view; spend the orange accent sparingly.
3. Show vocabulary with the watercolor `WordRow` — the paint is the brand.
4. Keep it paper: warm ivory, warm long shadows, hairline borders, soft rounding.
5. German UI uses formal "Sie"; learner-facing explanations are in Russian. No emoji.

If you are loading components outside this design-system environment, you can
copy the `.jsx` files and `assets/` into your project and import them directly;
inside a consuming design project, read them from the compiled bundle as the
`@dsCard` HTML files demonstrate.
