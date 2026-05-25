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
