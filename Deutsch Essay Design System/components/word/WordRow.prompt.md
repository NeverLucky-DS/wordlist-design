WordRow — the signature watercolor dictionary entry. Painted with its own brush by CEFR level × word-type, serif headword, italic gloss, level tag. The single most brand-defining component.

```jsx
<WordRow art="die" de="Abhängigkeit" ru="зависимость" pos="noun" level="B1" />
<WordRow de="analysieren" ru="анализировать" pos="verb" level="B2" />
<WordRow de="nachhaltig" ru="устойчивый" pos="adj" level="C1" active />
```

- The brush is chosen automatically from `level` + (`pos` or `art`). B1 rose / B2 blue / C1 lavender families.
- `active` reveals the full stroke (use for the opened word).
- Set `brushBase` to the relative path from your page to `assets/brushes/` (default `"assets/brushes/"`). Stack rows in a 1–3 column grid with ~10px row gap.
