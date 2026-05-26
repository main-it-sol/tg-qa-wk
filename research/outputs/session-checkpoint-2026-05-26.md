---
title: Session Checkpoint
date: 2026-05-26
type: checkpoint
---

# Session Checkpoint — 2026-05-26

Snapshot of where the research wiki sits and what's open. Hand this to a fresh session to skip the warmup.

## State of the wiki (committed in `6f12996`)

- **Sources:** `voice-backend-sketch.md` (from `research/raw/articles/voice-backend-sketch.md`)
- **Concepts:** `voice-session-state-machine`, `voice-wire-protocol`, `voice-activity-detection`, `barge-in`, `adapter-pattern-stt-llm-tts`
- **Entities, Comparisons:** none yet
- **Index + log:** initialized

All cross-links use `[[wikilinks]]` per `CLAUDE.md`. The source file was renamed from `articles/README.md` to `articles/voice-backend-sketch.md` after ingest — the original ingest log entry is preserved unchanged, with a separate rename entry appended.

## Open follow-ups offered to the user, not yet answered

1. **`research/wiki/concepts/testing-strategy.md`** — User asked "what types of testing are used in the project?" Answered from `backend/tests/` + `plan.md:89` (pytest + pytest-asyncio, unit / state-machine / WS-integration layers, hand-written fakes, synthetic PCM, no E2E yet). Offered to write a full concept page and back-link it from `[[voice-backend-sketch]]` and `[[adapter-pattern-stt-llm-tts]]`. User did not respond before checkpoint.

2. **Real `articles/README.md`** — After renaming the article out of the README slot, offered to write a folder-describing README at `research/raw/articles/README.md`. User did not respond before checkpoint.

## Conventions worth knowing (also saved as memories)

- **"publish changes"** = run `./publish_changes -c "<msg>"` (script at repo root, git-ignored). It does `git add .` → `git commit -m "$msg"` → `git push`. Always pass a real message via `-c` and include the `Co-Authored-By: Claude Opus 4.7 (1M context)` trailer.
- **Communication channel** is Telegram (chat_id `160646674`). Replies via the telegram MCP `reply` tool; edits don't push-notify so use a new reply for completions.
- **Wiki workflow** is the one in `/home/main/projects/virt-rav/CLAUDE.md` — Ingest / Query / Lint, with frontmatter and `[[wikilinks]]` required on every wiki page.

## Project structure quick reference

```
virt-rav/
  CLAUDE.md              wiki workflow spec
  SPEC.md                project spec
  plan.md                roadmap (line 89: testing summary)
  publish_changes        git-ignored bash script — DO NOT commit
  backend/
    pyproject.toml       pytest config (asyncio_mode = auto)
    src/virtrav/voice/   protocol.py, vad.py, adapters.py, session.py, ws.py
    tests/               test_protocol, test_vad, test_adapters,
                         test_session, test_ws + conftest.py
  research/
    raw/articles/voice-backend-sketch.md   only article so far
    wiki/                ingested content
    outputs/             this file lives here; PDFs are gitignored
```
