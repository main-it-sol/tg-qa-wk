---
title: Software Testing in Continuous Delivery (Atlassian)
type: source-summary
sources:
  - research/raw/articles/software-testing-continuous-delivery.md
related:
  - "[[testing-levels]]"
  - "[[testing-strategy]]"
  - "[[continuous-delivery]]"
  - "[[adapter-pattern-stt-llm-tts]]"
created: 2026-05-26
updated: 2026-05-26
confidence: high
---

# Software Testing in Continuous Delivery (Atlassian)

General-audience primer from Atlassian (published 2026-01-21) covering what software testing is, the standard levels of testing, and how that test suite plugs into a continuous delivery pipeline. Not specific to any language or framework. Useful as the project's reference for shared vocabulary around testing.

## Scope of the source

- Manual vs automated testing — definitions.
- The four conventional **levels** of testing: unit, integration, functional/E2E, exploratory. See [[testing-levels]].
- How a **CD pipeline** uses tests as the auto-merge / auto-deploy gate. See [[continuous-delivery]].
- A recommended **testing strategy** for GUI apps and the rationale for not chasing 100% coverage. See [[testing-strategy]].
- Cultural argument: developers own quality end-to-end; no separate QA silo.

## Key claims

- Tests reduce both development and maintenance cost. They give developers a fixed target ("done = passes these tests") and make later changes safer.
- Each level of testing has a distinct vantage point — they are complementary, not substitutes.
- 100% coverage is unrealistic under real timelines/budgets; **strategy is about choosing high-value coverage targets**, not maximizing a number.
- Test type should match deliverable: GUI apps benefit most from E2E on core flows; headless/library code benefits most from unit tests.
- CD pipelines collapse the historical Dev → QA → Release handoff into one automated path, which is also an org-design claim (fewer separate teams).

## What the source does *not* cover

- Specific frameworks, runners, or coverage tools (mentions only that they exist per language).
- Concrete pipeline configuration (CI tool setup is linked out, not described).
- Performance, load, security, or chaos testing — only the four "levels" above.
- Test-double taxonomy (mock vs fake vs stub) — only mentions mocking 3rd-party deps in passing.

## Relationship to the Virtual Rabbi project

The voice backend sketch already follows this strategy in spirit: [[adapter-pattern-stt-llm-tts]] exists specifically so the test suite runs against fakes (unit + integration territory), and the deliberately small four-state [[voice-session-state-machine]] is the kind of "data-sensitive" core flow that earns dedicated unit tests under the article's heuristic.

## Confidence

High for restating the article's content. The article itself is a general primer — its claims are conventional industry wisdom, not novel research, so they are weakly evidenced but widely accepted.
