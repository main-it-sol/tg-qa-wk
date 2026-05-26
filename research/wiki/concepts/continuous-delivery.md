---
title: Continuous Delivery
type: concept
sources:
  - research/raw/articles/software-testing-continuous-delivery.md
related:
  - "[[software-testing-continuous-delivery]]"
  - "[[testing-levels]]"
  - "[[testing-strategy]]"
created: 2026-05-26
updated: 2026-05-26
confidence: medium
---

# Continuous Delivery

Continuous delivery (CD) is the practice of running every code change through an automated pipeline that, if all tests pass, merges and deploys it to production — and, if any test fails, rejects the change and notifies the author. The test suite is the gate.

## The pipeline, per the source

> *An optimal setup would allow a developer to push recently completed code into the continuous delivery pipeline for evaluation. The pipeline would then run the newly pushed code through the levels of testing. If the code passes the testing, it will be automatically merged and deployed to production. If however, the code fails the tests, the code will be rejected and the developer automatically notified of steps to correct.*

This is the article's CD definition in one paragraph. Notable bits:

- **Single path.** There isn't a separate "ready for QA" intermediate stage — the pipeline either merges-and-deploys or rejects.
- **Test suite = gate.** The CD pipeline is only as trustworthy as the tests it runs. A weak suite produces a confident pipeline shipping broken code.
- **Author feedback.** Rejection includes "steps to correct" sent back to the developer — the loop is fast specifically so the author still has context.

## What CD requires of the test suite

- **All four levels** ([[testing-levels]]) — the source explicitly says CD "leverages all the aforementioned testing strategies."
- **Fast enough to gate every change** — implied. If the suite is slow, the gate becomes a bottleneck and people route around it.
- **Reliable.** Flaky tests in a CD pipeline are corrosive: every false fail erodes trust until people start ignoring real fails too. (The article doesn't say this explicitly — added as implication.)
- **Coverage chosen by [[testing-strategy]]**, not by coverage-percent target.

## Org-design implication

The source frames CD as an alternative to traditional handoff structures (separate QA, release management, test engineering). When tests are the gate, the developer who wrote the change owns proving its quality — there's no QA team to throw it over the wall to.

> *The organizational costs of hiring and managing separate teams for Quality Assurance, Release management, and Test engineering roles can be drastically cut with a commitment to a CD workflow.*

This is partly a cost argument and partly a quality argument: the source's claim is that **developer empathy with end users improves when developers can't offload quality**.

## Customer-feedback loop

CD's rapid deployment lets a team incorporate user feedback into the next release quickly. When a user reports an issue, the CD suite itself becomes a debugging aid — running the failing flow through the existing tests narrows the search space for the bug.

## What this concept doesn't cover

- The difference between continuous *delivery* and continuous *deployment* — the article uses CD loosely; in stricter usage, delivery = always shippable, deployment = automatically shipped.
- Branching models (trunk-based, GitFlow) and how they interact with the pipeline gate.
- Progressive delivery (feature flags, canaries, blue/green) — not in the source.
- Rollback strategy when a failure escapes the suite into production.

## Confidence

Medium for the source's specific claims (one general-audience article, conventional but not deeply argued). The CD-as-test-gated-pipeline definition is mainstream, so the core claim is on solid ground; the org-design claims are more contested in practice than the article admits.
