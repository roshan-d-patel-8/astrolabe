# The Astrolabe

The unified interface for Roshan's Axis Mundi: seven Focus Mundi altitudes, two wings, ten life and work domains, the dashboard fleet, a bowling chart, and the active TaskNotes board in one persistent spatial workspace.

## Product model

- **F0 Ground** — presence and the RAIN reset.
- **F1 Compass** — Polaris, mission, vision, and value dyads.
- **F2 Cartography** — an interactive Hathi/Skoll domain constellation.
- **F3 Monocle** — current condition and all 28 dashboard instruments.
- **F4 Lens** — pillar-anchored DRIVE/WATCH/LOOP measures.
- **F5 Momentum** — the live-at-build TaskNotes `gate → forge → flow` board.
- **F6 Andon** — capacity gates and leader standard work.

The altitude rail changes the granularity without changing the underlying context. Selecting a domain or task writes its lineage into the persistent trace strip. `/` opens global search; `0`–`6`, `[` and `]` navigate scale.

## Vault sync contract

TaskNotes remains canonical. `build.py` applies the professional-task exclusions from `TaskNotes/Views/kanban-default.base`, ingests the active task files plus dashboard frontmatter, and embeds that snapshot inside the encrypted payload. The static GitHub Pages copy never pretends it can write directly to local Markdown: task and dashboard surfaces deep-link to their authoritative Obsidian notes.

```bash
python3 build.py --preview  # regenerate .preview.html for local QA
python3 build.py            # rebuild encrypted index.html
python3 build.py --push     # rebuild, commit, push, and verify index.html
```

The canonical content source is `Artificial Intelligence/Executive Assistant/The Astrolabe.html` in the Obsidian vault. This repo carries the public interaction layer (`app.js`, `app.css`), encrypted payload, unlock shell, build pipeline, and browser smoke tests. The payload is AES-256-GCM encrypted with PBKDF2-SHA256 at 310,000 iterations and decrypts in the browser. Observatory answers persist only in browser storage until explicitly copied back.
