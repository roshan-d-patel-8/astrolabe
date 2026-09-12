---
tags: [ClaudeAI]
---
# The Astrolabe

The unified visual-management interface for Roshan's Axis Mundi: five Focus Mundi altitudes, two wings, ten domains, dashboard instruments, recorded measures, and active TaskNotes work in one persistent workspace.

## Product model

- **F1 Compass** — Polaris, mission, vision, and value dyads.
- **F2 Cartography** — strategic/mental-model instruments and paired domain plates; domain context carries across the focus levels.
- **F3 The Real** — lived experience, temporal perspective, and source evidence; instrument refresh age remains a secondary metadata view, not a health rating.
- **F4 Lens** — recorded readings, targets, categorical status, and ownership; explicitly not live telemetry.
- **F5 Momentum** — TaskNotes projects, date windows, priorities, and the `gate → forge → flow` board; explicit creation and updates in connected mode.

The altitude rail changes granularity without changing the underlying context. The working-atlas design uses aligned rows, direct labels, proportional count bars, restrained signal color, and detail on demand. F5 supports stage and priority filters. `/` opens global search; `1`–`5`, `[` and `]` navigate scale. Both themes support mobile layouts, reduced motion, and keyboard-operated details/search. Celestial WebGL is active only while F1 is visible.

## Vault sync contract

TaskNotes remains canonical. `build.py` applies the professional-task exclusions from `TaskNotes/Views/kanban-default.base`, ingests the active task files plus dashboard frontmatter, and embeds that snapshot inside the encrypted payload. The static GitHub Pages copy never pretends it can write directly to local Markdown: task and dashboard surfaces deep-link to their authoritative Obsidian notes.

All 28 registered dashboard instruments have curated focus/domain routes in `instruments.py`. Their source HTML and CSS are captured inside the encrypted payload and opened in a sandboxed in-site workspace. Scripts, external media, and Obsidian query/base execution are unavailable in that capture and labeled accordingly. The canonical note remains available. New unmapped dashboards fail the build until given intentional relationships.

### Connected mode on this Mac

Double-click **Open connected Astrolabe.command**, or run `python3 companion.py` from this folder. Open `http://127.0.0.1:8795/`. Keep its terminal running; closing it stops the companion. This is not an installed login service and is not exposed to the network.

The local workspace rereads TaskNotes on window focus and every 60 seconds while visible and no editor is open. Status, priority, scheduled date, due date, and parentProject edits are saved only after explicit submission. New Skoll tasks/projects begin in Gate with initialization date, tags, selected realm, and backlinks. Project records are separate from active task counts. No canonical user note is changed by the test suite.

Writes require the same origin, exact loopback Host, and per-session token. The service accepts only whitelisted fields against IDs resolved from the active canonical board. Revision conflicts reject stale edits. Prior note contents are saved in the vault's private `.astrolabe-backups/` folder before an atomic replacement; restore a backup's contents to the corresponding original note if needed. These backups and captures are never added to this repository. Obsidian Sync remains responsible for syncing the vault between devices.

Public Pages updates only after an encrypted rebuild/release. It has no write token and does not automatically receive local edits. Browser interview answers are device-local, not TaskNotes data.

```bash
python3 build.py --preview  # regenerate .preview.html for local QA
python3 build.py            # rebuild encrypted index.html
python3 build.py --push     # rebuild, commit, push, and verify index.html
```

The canonical content source is `Artificial Intelligence/Executive Assistant/The Astrolabe.html` in the Obsidian vault. This repo carries the public interaction layer (`app.js`, `atlas.css`), encrypted payload, unlock shell, build pipeline, and browser tests. The payload is AES-256-GCM encrypted with PBKDF2-SHA256 at 310,000 iterations and decrypts in the browser. Observatory answers persist only in browser storage until explicitly copied back.

Domain task counts are keyword-based suggestions. Unmatched tasks remain available in Momentum; Hathi tasks are excluded rather than counted as zero. Metric readings preserve the planning source and have no observation timestamps. Build timestamps must never be substituted for observation dates.

## Verification

Serve the repository locally after a preview build, then run `tests/smoke.py`, `tests/makeover.py`, and `tests/encrypted_smoke.py`. The makeover suite checks all five altitudes across four widths and both themes, domain/wing filtering, count proportions including zero, modal focus, search, and blocked browser storage. The encrypted test uses the existing Keychain entry without logging its value.

`tests/integration.py` verifies all instrument routes, Chronos in F1/F3/F5, source isolation, project/date filters, and public write boundaries. `tests/companion.py` creates a temporary fixture vault and verifies browser create/edit, note-body preservation, backups, conflicts, and Host/Origin/token/path/value rejection.

Impeccable's design guidance informed v3. Its CLI engine was unavailable in this environment; no automated Impeccable certification is claimed. The design review uses its craft-floor checklist.

## Backlinks

[[The Astrolabe]] · [[Focus - Axis Mundi]] · [[The Bridge]]
