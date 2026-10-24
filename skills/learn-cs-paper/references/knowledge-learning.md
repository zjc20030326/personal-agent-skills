# Knowledge and learning contract

## Knowledge classes

Classify each concept as:

1. **Prerequisite:** required before the relevant paper passage can be understood.
2. **Core:** required to understand the paper's method, evidence, or contribution.
3. **Extension:** useful after the paper for comparison, later developments, or research transfer.

For every concept record:

| Field | Requirement |
|---|---|
| Why needed | Name the exact paper dependency |
| Location | Link the section, paragraph, equation, figure, table, or code location |
| Mastery depth | Recognition, explanation, derivation, implementation, debugging, or transfer |
| Learning evidence | Specify a derivation, code task, exercise, or explanation |
| Relations | Link prerequisite, sibling, later-paper, and application concepts |
| Status | Not started, learning, retry required, or mastered with evidence |

## Reuse public knowledge notes

Use `知识库/计算机/机器学习/` for stable concepts reusable across papers. Keep paper-specific explanations inside the paper workspace.

Before creating a public note:

1. Search filenames and normalized aliases.
2. Inspect YAML `aliases` and existing Wikilinks/backlinks.
3. Prefer the canonical existing note when identity is clear.
4. Preserve existing text and links.
5. Append a source-labeled section naming the paper, exact location, and source block link.
6. When explanations conflict, keep both in an Obsidian callout with provenance; do not silently reconcile them.
7. Create a new public note only when the concept is stable, reusable, and no canonical note exists.

Never overwrite manual notes. Do not turn a paper-specific architectural detail into a generic public concept without evidence that it transfers.

## Paper knowledge map

In `04-知识地图.md`, link each prerequisite, core, and extension concept to its public note or a paper-local section. Record the dependency order and the next concept selected for study. Keep claims about the learner separate from content coverage.

## One-question mastery loop

1. Select one coherent concept at the learner's current level and focus.
2. Choose exactly one question type: retrieval, derivation, implementation, or transfer.
3. Ask the question without its answer and wait.
4. Diagnose only what the response demonstrates: missing fact, broken link, algebraic step, shape error, implementation misconception, or transfer failure.
5. Repair the smallest missing piece with a linked explanation or worked micro-step.
6. Ask for a retry of the same skill at comparable difficulty.
7. Record the learner attempt, diagnosis, repair, retry, and evidence in `07-互动学习记录.md`.

Do not batch questions. Do not infer mastery from agreement, reading, note completion, a study plan, or seeing the answer.

## Evidence for mastery

Use evidence matched to the target depth:

- **Explanation:** accurate mechanism and boundaries in the learner's own words.
- **Derivation:** correct assumptions, intermediate steps, and conclusion.
- **Implementation:** code produced or repaired by the learner and directly executed with relevant tests.
- **Debugging:** diagnosis linked to an observed failure and a verified correction.
- **Transfer:** correct application to a new architecture, dataset, setting, or counterexample.

Mark mastered only after a successful retry or transfer. Record the exact evidence and date; otherwise keep the status as learning or retry required.
