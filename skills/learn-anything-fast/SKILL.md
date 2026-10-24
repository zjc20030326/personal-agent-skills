---
name: learn-anything-fast
description: Use when a user wants to quickly learn, research, understand, practice, review, or test mastery of an unfamiliar topic under a time budget, especially for a learning path, study sprint, resource shortlist, oral exam, Feynman explanation loop, or one-page cheat sheet.
---

# Learn Anything Fast

## Overview

Turn “learn this topic” into an adaptive, evidence-aware loop with a concrete performance target. Optimize for verified understanding and usable output, not the amount of content produced.

## Start with a learning brief

Extract these fields from the request before teaching:

| Field | Required question |
|---|---|
| Topic | What topic or concept is in scope? |
| Target | What must the learner be able to explain, solve, build, or decide? |
| Starting point | What can the learner already do, and what prerequisites are missing? |
| Budget | How much time is available now and before the deadline? |
| Evidence | What artifact or performance will prove mastery? |
| Constraints | Which language, tools, sources, depth, or output format matters? |

Infer fields already supplied. Ask only the single missing question that would materially change the route; otherwise state the assumptions and begin.

## Route by intent

| User intent | Route |
|---|---|
| Understand a field before committing | Stages 1–4 |
| Choose resources and make a plan | Stages 5–7 |
| Learn through guided practice | Stages 6, 7, 9 |
| Test real understanding | Stages 8–9 |
| Refresh before use | Stage 10 |
| “Learn this thoroughly” | Stages 1–10 in checkpoints |

Read [references/stage-contracts.md](references/stage-contracts.md) for the selected stages. Do not run all 10 stages merely because they exist. For a full route, deliver one phase at a time and pause at a meaningful checkpoint.

## Execute the learning loop

1. **Map**: Use multiple perspectives, contradictions, synthesis, and peer review to establish what is known and disputed.
2. **Design**: Curate a small resource set, build a five-level ladder, and isolate the highest-leverage 20%.
3. **Practice**: Require recall, explanation, calculation, construction, or a small project.
4. **Diagnose**: Classify the exact gap rather than saying only “wrong” or “review more.”
5. **Repair**: Reteach only the missing link, then ask for a new attempt.
6. **Compress**: Produce a one-page retrieval aid only after the learner has worked with the material.

Treat planning, reading, and recognition as inputs—not proof of mastery. Advance only when the learner produces the milestone artifact or passes the stage check.

## Preserve interaction

- For an oral exam, ask exactly one question, wait, score the response, explain the precise gap, then adapt the next question.
- For a Feynman loop, explain simply, request the learner’s restatement, repair only ambiguous or missing links, and repeat before introducing new content.
- For a study sprint, show the timebox and success criteria first. Teach in short blocks with an exercise or recall check after each block.
- For a multi-day path, make the first response a route summary plus the first work block. Defer detailed later-day instruction until a checkpoint unless the user explicitly requests a complete printable plan.
- Do not reveal model answers before the learner attempts a retrieval task.
- Do not replace practice with an oversized study plan.

## Keep evidence honest

- Treat the five perspectives as analytical lenses, not invented authorities.
- Distinguish established evidence, reasoned inference, practitioner experience, and speculation.
- Search current primary or authoritative sources when the user asks for resources, papers, software, standards, high-stakes guidance, or other information that can drift.
- Give the strongest counterargument, not a caricature. State what evidence would change the conclusion.
- Replace a default lens when it is irrelevant to the topic, and explain the substitution.
- Never claim code, a resource, or a learning result was verified unless direct tool evidence was obtained in the current turn. Otherwise label it “not live-verified” and provide a verification command or checkpoint.

## Output contract

Lead with:

1. the chosen route;
2. the learner’s target and assumptions;
3. the next concrete action;
4. the observable completion criterion.

For an interactive request, the first response should contain only the route summary, the first teaching or practice block, and one next prompt. Do not front-load every later lesson.

End each non-interactive phase with:

- **What you should now be able to do**
- **One retrieval check**
- **One artifact or exercise**
- **The next branch based on the result**

## Quick examples

- “I have 2 hours to learn diffusion models” → run Stage 7 in short interactive blocks; do not print all lessons and answers at once.
- “Help me evaluate whether I understand Bayes’ theorem” → run Stage 8 and ask only Question 1.
- “I need to research a controversial field” → run Stages 1–4 with sourced evidence and explicit uncertainty.
- “Make me a one-week path to read papers and build a Python demo” → combine Stages 5–7 and define a runnable project as the mastery artifact.

## Common mistakes

| Mistake | Correction |
|---|---|
| Producing all 10 stages in one huge answer | Route to the minimum useful stages and use checkpoints. |
| Asking several diagnostic questions at once | Ask one high-information question or proceed with stated assumptions. |
| Giving five confident voices without evidence | Use lenses, cite support, and expose uncertainty. |
| Recommending popular resources without checking them | Verify availability, authority, level, and fit. |
| Calling completion of a schedule “mastery” | Require recall, transfer, or a working artifact. |
| Giving five exam questions at once | Ask exactly one, wait, score, repair, adapt. |
