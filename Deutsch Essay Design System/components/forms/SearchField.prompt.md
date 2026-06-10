SearchField — the brand text input, framed as search. Leading icon, soft hairline, accent focus ring.

```jsx
<SearchField value={q} onChange={e => setQ(e.target.value)}
  placeholder="Suche nach Begriff oder Übersetzung" />
```

- `size`: `md` (52px, page search) or `sm` (40px, panel search).
- `icon`: omit for the search glyph; pass `null` for a plain text field; pass a node to customise.
