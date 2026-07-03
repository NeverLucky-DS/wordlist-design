Button — the brand's primary action; muted-plum gradient for the one key action, paper outline for secondary, ghost for tertiary.

```jsx
<Button variant="primary" size="lg" icon={<SparkleIcon />}>Analysieren</Button>
<Button variant="secondary">Neues Essay</Button>
<Button variant="ghost">Abbrechen</Button>
```

- `variant`: `primary` (gradient + glow, max one per view), `secondary` (white card, hairline → accent on hover), `ghost` (quiet).
- `size`: `md` (default, 46px) or `lg` (50px, hero CTAs).
- `icon`: optional leading SVG node.
- `disabled` dims to 0.55 and drops the glow.
