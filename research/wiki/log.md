# Operation Log

Append-only. Newest entries at the bottom.

## 2026-05-25 — Ingest: voice-backend-sketch

- **Operation:** ingest
- **Source:** `research/raw/articles/README.md` ("Virtual Rabbi — voice backend sketch")
- **Notes:** Source is named `README.md` because it doubles as the article and as the description of the `articles/` folder for this first ingest; user confirmed it should be treated as the article.
- **Pages created:**
  - `sources/voice-backend-sketch.md`
  - `concepts/voice-session-state-machine.md`
  - `concepts/voice-wire-protocol.md`
  - `concepts/voice-activity-detection.md`
  - `concepts/barge-in.md`
  - `concepts/adapter-pattern-stt-llm-tts.md`
- **Index:** initialized.

## 2026-05-25 — Rename source file

- **Operation:** rename
- **From:** `research/raw/articles/README.md`
- **To:** `research/raw/articles/voice-backend-sketch.md`
- **Reason:** Source file was occupying the `README.md` slot; freed it for an actual folder readme.
- **Updated:** `sources` frontmatter in all 6 wiki pages and the `Source:` pointer in `index.md` re-pointed to the new path.

## 2026-05-26 — Ingest: software-testing-continuous-delivery

- **Operation:** ingest
- **Source:** `research/raw/articles/software-testing-continuous-delivery.md` (Atlassian, "Software Testing in Continuous Delivery", published 2026-01-21).
- **Pages created:**
  - `sources/software-testing-continuous-delivery.md`
  - `concepts/testing-levels.md`
  - `concepts/testing-strategy.md` (closes the previously-open follow-up to write this page)
  - `concepts/continuous-delivery.md`
- **Pages updated:**
  - `concepts/adapter-pattern-stt-llm-tts.md` — added `[[testing-levels]]` and `[[testing-strategy]]` to `related`, bumped `updated`, and added one sentence framing the adapter setup in terms of those concepts.
  - `index.md` — added the new source and three concepts.
- **Notes:** Decided against splitting unit/integration/E2E/exploratory into four separate pages — each is too thin on its own in the source; one `testing-levels` page reads better and matches how the source presents them. `test-coverage` not given its own page (one paragraph in the source); folded into `testing-strategy`.

## 2026-05-26 — Lint

- **Operation:** lint (focus: contradictions + stale claims, per user request).
- **Output:** `research/outputs/lint-2026-05-26.md`.
- **Findings summary:** 0 contradictions; 1 stale claim affecting 3 pages (`src/virtrav/voice/*` paths missing the `backend/` prefix; code has since landed under `backend/`); 1 minor prose imprecision in `voice-activity-detection.md`; no orphans; no broken wikilinks.
- **No wiki pages edited** in this lint pass — report only. Fixes are suggested in the output file and await user direction.
