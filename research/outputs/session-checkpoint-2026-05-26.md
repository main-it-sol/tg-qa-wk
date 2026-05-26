---
title: Session Checkpoint
date: 2026-05-26
type: checkpoint
---

# Session Checkpoint — 2026-05-26 (evening)

Snapshot of where the research wiki sits and what's open. Hand this to a fresh session to skip the warmup. Supersedes the earlier same-day checkpoint (its prior content is preserved in git at commit `6f12996`).

## State of the wiki (latest commit: `a3f129f`)

**Sources (2):**
- `voice-backend-sketch.md` ← `research/raw/articles/voice-backend-sketch.md`
- `software-testing-continuous-delivery.md` ← `research/raw/articles/software-testing-continuous-delivery.md` (Atlassian, ingested this session)

**Concepts (8):**
- Voice cluster: `voice-session-state-machine`, `voice-wire-protocol`, `voice-activity-detection`, `barge-in`, `adapter-pattern-stt-llm-tts`
- Testing cluster (new this session): `testing-levels`, `testing-strategy`, `continuous-delivery`

**Entities, Comparisons:** none yet.

**Bridge between clusters:** only `adapter-pattern-stt-llm-tts` links voice ↔ testing (via `related` and one inline paragraph added this session).

**Index + log:** in sync with filesystem; `log.md` now has 4 entries (initial ingest, source-file rename, 2nd ingest, lint pass).

## What this session did

1. Ingested the Atlassian "Software Testing in Continuous Delivery" article → 4 new wiki pages, backlinked from the adapter page, index/log updated.
2. Ran a contradictions/stale-claims lint → `research/outputs/lint-2026-05-26.md`. Zero contradictions; 1 stale claim (3 pages cite `src/virtrav/voice/*.py` but actual code lives at `backend/src/virtrav/voice/*.py`); 1 minor prose imprecision in `voice-activity-detection.md`.
3. Made `./publish_changes` executable (`chmod +x`); git tracked no mode change, working tree clean.
4. Published the ingest+lint changes as `a3f129f`.

## Open follow-ups (carrying forward)

1. **Stale-path fixes (lint F1).** Three wiki pages still cite `src/virtrav/voice/…` instead of `backend/src/virtrav/voice/…`. User said *"don't fix paths now"* — defer until requested. Full detail in `research/outputs/lint-2026-05-26.md`.
2. **Broader code-vs-doc audit.** The lint only checked paths. Sketch-derived claims about wire-protocol bytes, state-machine transitions, and adapter ABC shapes may have drifted from the actual `backend/src/virtrav/voice/*.py` code. Offered in the lint report, not greenlit.
3. **Minor prose fix (lint F2).** `voice-activity-detection.md` line 17 oversimplifies speech_start/speech_end transitions. Low priority.
4. **Real `articles/README.md`.** Carried over from prior session. The `README.md` slot in `research/raw/articles/` is empty after the original source was renamed. User has not asked for this.

## Memory state

- `project_open_followups.md` updated this session: testing-strategy follow-up marked resolved; `articles/README.md` follow-up still open.
- `feedback_publish_changes.md` still current (used this session — `./publish_changes -c "<msg>"`).
- No new memories written this session beyond the follow-up update.

## Conventions worth knowing (also saved as memories)

- **"publish changes"** = `./publish_changes -c "<msg>"` at repo root. As of this session the script is `chmod +x`-ed. The script does `git add .` → `git commit -m "$msg"` → `git push`. Always pass a real `-c` message including the `Co-Authored-By: Claude Opus 4.7 (1M context)` trailer.
- **Communication channel** = Telegram, chat_id `160646674`. Reply via the telegram MCP `reply` tool. Edits don't push-notify, so always send a new reply when work completes.
- **Wiki workflow** is in `/home/main/projects/virt-rav/CLAUDE.md` — Ingest / Query / Lint, with frontmatter + `[[wikilinks]]` required on every wiki page.
- **Ingest etiquette** (validated this session): propose page split via Telegram before writing, then proceed once user confirms. Don't unilaterally fan a single short source out into many thin pages — bundle when topics are too thin individually.

## Project structure quick reference

```
virt-rav/
  CLAUDE.md              wiki workflow spec
  SPEC.md                project spec
  plan.md                roadmap (line 89: testing summary)
  publish_changes        bash script — now executable; git-ignored, don't commit
  backend/
    pyproject.toml       pytest config (asyncio_mode = auto)
    src/virtrav/voice/   protocol.py, vad.py, adapters.py, session.py, ws.py
    tests/               test_protocol, test_vad, test_adapters,
                         test_session, test_ws + conftest.py
  research/
    raw/articles/        voice-backend-sketch.md
                         software-testing-continuous-delivery.md  ← new
    wiki/                10 content pages (2 sources, 8 concepts) + index + log
    outputs/             this file + lint-2026-05-26.md; PDFs gitignored
```
