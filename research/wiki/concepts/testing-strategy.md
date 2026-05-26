---
title: Testing Strategy
type: concept
sources:
  - research/raw/articles/software-testing-continuous-delivery.md
related:
  - "[[software-testing-continuous-delivery]]"
  - "[[testing-levels]]"
  - "[[continuous-delivery]]"
  - "[[adapter-pattern-stt-llm-tts]]"
created: 2026-05-26
updated: 2026-05-26
confidence: high
---

# Testing Strategy

A testing strategy is the decision of **where to spend test effort**, given that 100% coverage is unrealistic under real budgets and timelines. The strategy is shaped by product type, business risk, and the deliverable's surface area — not by maximizing any single metric.

## Core principle from the source

> *In an ideal world, a software project would strive for 100% test coverage … Unfortunately in the real business world, with timelines and budget constraints, this is not so realistic.*

Translation: **coverage is a means, not a goal.** Pick coverage targets by value, not by what's easiest to instrument.

## Heuristic: test type follows deliverable type

| Deliverable | Highest-value test type |
|---|---|
| GUI-driven app | End-to-end tests on core user flows |
| Headless / library code | Unit tests |
| Anything talking to 3rd-party services | Integration tests on those boundaries |
| Code touching money or other sensitive data | Unit tests, exhaustive |

See [[testing-levels]] for the level definitions.

## Recommended GUI-app strategy (verbatim from source)

1. **End-to-end** tests on all core user flows: login, signup, checkout, etc.
2. **Unit** tests on all data-sensitive code functions (e.g., monetary transactions).
3. **Integration** tests at every point of third-party integration — to ensure data is flowing to the third party and errors are propagating back correctly.

Note the asymmetry: E2E coverage is *broad* (every core flow), unit coverage is *deep* (every data-sensitive function), integration coverage is *targeted* (every external seam). They are not interchangeable — substituting one for another loses the property each is good at.

## What "coverage" means here

The article touches on test coverage tools (linking out to Atlassian's Clover) but doesn't define coverage rigorously. The strategy framing implicitly treats coverage as a **per-flow / per-function decision**, not a percent-of-lines target. The two views aren't equivalent: line coverage can be high while every important flow is still untested, and vice versa.

## Cultural prerequisite

The source pairs strategy with **developer ownership of quality**: the same person writing the feature is responsible for proving its quality. The strategy collapses if test ownership is offloaded to a separate QA team that wasn't in the design conversation — they can't know which functions are "data-sensitive" or which flows are "core" without re-discovering them.

See [[continuous-delivery]] for how the strategy plugs into an automated pipeline.

## Application to this project

The Virtual Rabbi voice backend ([[voice-backend-sketch]]) is closer to "headless library code" than to a GUI app, so the source's heuristic suggests **unit-heavy** with **integration at the STT/LLM/TTS seams** — which is what [[adapter-pattern-stt-llm-tts]] already enables (fakes for all three adapters). E2E voice tests are not in the sketch's scope; if a 2D avatar/UI lands later, the strategy heuristic flips and E2E on the voice-loop UX becomes the high-value target.

## What this concept doesn't cover

- Non-functional tests (performance, load, security, chaos) — the source's strategy is silent on these, which is itself a gap worth flagging.
- Test-double taxonomy (mock vs fake vs stub).
- How to *retire* tests that have become low-value.
