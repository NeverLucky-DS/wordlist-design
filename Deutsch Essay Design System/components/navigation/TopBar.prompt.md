TopBar — the shared, frosted, sticky site header used on every product surface.

```jsx
<TopBar
  initial="D"
  items={[
    { label: 'Dashboard' },
    { label: 'Schreiben', active: true },
    { label: 'Lernen', dropdown: true },
    { label: 'Verlauf' },
    { label: 'Pipeline' },
  ]}
/>
```
- Brand defaults to "Deutsch / Essay" (stacked). Mark one nav item `active` for the orange underline.
- `right` overrides the whole right cluster; omit for the default theme toggle · avatar · language pill.
