# Code graph (for AI navigation)

The repo ships with a **Graphify** code-graph — a structural map of files, symbols, and
their relationships. Use it to answer "what touches X?" / "where does this flow go?" faster
than grepping the whole tree.

## Where it lives

`graphify-out/` (git-ignored, generated locally — not committed):

| File | Use |
|------|-----|
| `GRAPH_REPORT.md` | **Start here** — human/AI-readable summary: node/edge counts, community hubs (navigation entry points), freshness. |
| `graph.json` | Full node/edge data (nodes = files/symbols, edges = calls/imports/refs). |
| `graph.html` | Interactive visual graph (open in a browser). |
| `manifest.json` | File → node/label index. |
| `cache/` | AST cache (speeds up re-runs; safe to delete). |

## Freshness (check before trusting it)

The report records the commit it was built from:

```bash
grep "Built from commit" graphify-out/GRAPH_REPORT.md   # -> e.g. `dd7134a5`
git rev-parse HEAD                                       # compare
```

If they differ, the graph is stale. Refresh (no API cost):

```bash
graphify update .
```

After large structural changes (moved/renamed/removed files) run the same command so the
graph and `GRAPH_REPORT.md` stay in sync with `info/CRITICAL-LINKS.md`.

## How to use it

1. Open `GRAPH_REPORT.md` → **Community Hubs** lists the most-connected nodes
   (`runner.py`, `schreiben.js`, `app.js`, `mistral_analyzer.py`, `Word`, `WordTopic`, …).
   These are the natural entry points into each subsystem.
2. To trace dependencies of a specific file/symbol, query `graph.json` for its node and
   follow incoming/outgoing edges.
3. Cross-check risky edits against [CRITICAL-LINKS.md](CRITICAL-LINKS.md) — the hand-maintained
   safe-delete map is authoritative when it disagrees with the auto-graph.
