---
title: Levels of Software Testing
type: concept
sources:
  - research/raw/articles/software-testing-continuous-delivery.md
related:
  - "[[software-testing-continuous-delivery]]"
  - "[[testing-strategy]]"
  - "[[continuous-delivery]]"
  - "[[adapter-pattern-stt-llm-tts]]"
created: 2026-05-26
updated: 2026-05-26
confidence: high
---

# Levels of Software Testing

Per [[software-testing-continuous-delivery]], software tests are conventionally organized into four levels, each looking at the system from a different vantage point. They are complementary — a project usually wants some of each, not one to the exclusion of others.

## Unit testing

Tests a single function/method in isolation. Production code is executed in a test environment with simulated input, and the output is compared against the expected value.

- **Vantage point:** the individual code unit, no collaborators.
- **Strongest at:** validating derived-data functions, especially anything with a precise mathematical or business rule (monetary math is the article's example).
- **Example shape (from the source):** `function 2VAL(x, y) → x+y`; the test calls it with two values and asserts the sum.

## Integration testing

Tests that cross more than one unit. The article notes that the line is fluid — a "unit" test that talks to a third-party library is effectively an integration test, and the third-party side is typically mocked or faked.

- **Vantage point:** the seam between units, or between your code and an external dependency.
- **Strongest at:** boundaries — DB, queue, third-party API, in-process module composition.

## Functional / end-to-end testing

Drives the full user-level experience through tools that simulate human interaction (click button, read text, submit form).

- **Vantage point:** the whole stack, top to bottom.
- **Strongest at:** verifying that the integrated system actually delivers a flow — login, signup, checkout — under conditions close to production.

## Exploratory testing

Loosely-scripted human exploration. Testers are given a goal and wander, rather than running a fixed script. Not the same as unstructured "random" testing — it's intentional, just not pre-written.

- **Vantage point:** the user, with judgment.
- **Strongest at:** surfacing problems automation didn't think to check, especially UX issues and unexpected usage patterns. The article notes it scales easily because "anyone can join in."

## How they relate

The four levels narrow → widen in *scope*, and widen → narrow in *speed*:

| Level | Scope | Typical speed | Typical author |
|---|---|---|---|
| Unit | one function | ms | developer |
| Integration | a few collaborators | ms–s | developer |
| Functional / E2E | full stack | s–min | dev or QA |
| Exploratory | full stack + human judgment | minutes per session | anyone |

How to *choose* a mix of these for a given project is the subject of [[testing-strategy]]. How they fit into automated delivery is in [[continuous-delivery]].

## Application to this project

In the Virtual Rabbi voice backend ([[voice-backend-sketch]]), the [[adapter-pattern-stt-llm-tts]] split is set up specifically so the test suite can stay in the unit + integration tier (fakes only, no GPU/network). End-to-end voice tests are not described in the sketch.
