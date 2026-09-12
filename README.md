# The Astrolabe

The unified visual-management interface for Roshan's Axis Mundi: five Focus Mundi altitudes, two wings, ten domains, dashboard instruments, recorded measures, and active TaskNotes work in one persistent workspace.

## Product model

- **F1 Compass** — Polaris, mission, vision, and value dyads.
- **F2 Cartography** — paired Hathi/Skoll domain plates; selection carries into F4 and F5.
- **F3 The Real** — instrument refresh metadata plotted on a common age scale, not a data-health rating.
- **F4 Lens** — recorded readings, targets, categorical status, and ownership; explicitly not live telemetry.
- **F5 Momentum** — TaskNotes flow, priority distribution, and the live-at-build `gate → forge → flow` board.

The altitude rail changes granularity without changing the underlying context. The working-atlas design uses aligned rows, direct labels, proportional count bars, restrained signal color, and detail on demand. F5 supports stage and priority filters. `/` opens global search; `1`–`5`, `[` and `]` navigate scale. Both themes support mobile layouts, reduced motion, and keyboard-operated details/search. Celestial WebGL is active only while F1 is visible.

## Vault sync contract

TaskNotes remains canonical. `build.py` applies the professional-task exclusions from `TaskNotes/Views/kanban-default.base`, ingests the active task files plus dashboard frontmatter, and embeds that snapshot inside the encrypted payload. The static GitHub Pages copy never pretends it can write directly to local Markdown: task and dashboard surfaces deep-link to their authoritative Obsidian notes.

```bash
python3 build.py --preview  # regenerate .preview.html for local QA
python3 build.py            # rebuild encrypted index.html
python3 build.py --push     # rebuild, commit, push, and verify index.html
```

The canonical content source is `Artificial Intelligence/Executive Assistant/The Astrolabe.html` in the Obsidian vault. This repo carries the public interaction layer (`app.js`, `atlas.css`), encrypted payload, unlock shell, build pipeline, and browser tests. The payload is AES-256-GCM encrypted with PBKDF2-SHA256 at 310,000 iterations and decrypts in the browser. Observatory answers persist only in browser storage until explicitly copied back.

Domain task counts are keyword-based suggestions. Unmatched tasks remain available in Momentum; Hathi tasks are excluded rather than counted as zero. Metric readings preserve the planning source and have no observation timestamps. Build timestamps must never be substituted for observation dates.

## Verification

Serve the repository locally after a preview build, then run `tests/smoke.py`, `tests/makeover.py`, and `tests/encrypted_smoke.py`. The makeover suite checks all five altitudes across four widths and both themes, domain/wing filtering, count proportions including zero, modal focus, search, and blocked browser storage. The encrypted test uses the existing Keychain entry without logging its value.

Impeccable's design guidance informed v3. Its CLI engine was unavailable in this environment; no automated Impeccable certification is claimed. The design review uses its craft-floor checklist.
