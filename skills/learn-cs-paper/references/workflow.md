# Workflow contract

## 1. Establish the route

Infer `source`, `goal`, `focus`, `level`, `time_budget`, `output_mode`, `code_level`, `modern_context`, `vault`, and `collection`. Record every nontrivial assumption in the MOC. Ask one question only when its answer changes source acquisition, the output route, or the reproduction gate.

Use these defaults: graduate-entry depth, `output_mode=混合`, `code_level=最小实现`, concise modern context, Vault `D:\Markdown\Obsidian\Obsidian-Notes`, and collection `论文\机器学习`.

## 2. Select and bind the source

1. Prefer a supplied/local PDF, then a Zotero attachment, an arXiv or author-public copy, and finally a DOI page the user can lawfully access.
2. Identify title, authors, year, venue, DOI/arXiv identifier, version label or date, retrieval date, and PDF SHA-256.
3. Compare the selected PDF with `assets/paper-manifest.json` before writing.
4. Treat metadata and abstract-only access as an incomplete source. Do not start full translation.
5. Record discrepancies between versions; do not silently pick or merge passages.

## 3. Resume from the manifest

| Observed state | Action |
|---|---|
| No workspace | Run the bundled initializer |
| Workspace and manifest, same hash | Resume the first incomplete checkpoint without rebuilding existing Markdown |
| Same title, changed hash | Use the initializer-selected hash-suffixed sibling workspace |
| Directory exists without manifest | Refuse takeover and ask the user to inspect or choose another location |
| Manifest is unreadable or inconsistent | Stop writes, report the validation/loading failure, and preserve files |

Read `progress`, `validated_sections`, `uncertainties`, source metadata, structure lists, and counts. Re-check the source when retrieval date, version, or hash is ambiguous.

## 4. Stage A — reference workspace

Complete in this order:

1. Initialize the workspace and bind the source/version.
2. Extract and record the ordered inventory of sections, paragraphs, equations, algorithms, figures, tables, appendices, and references.
3. Establish stable section/paragraph IDs and the terminology table.
4. Produce bilingual files in source order; record OCR, reading-order, formula, and page uncertainties.
5. Validate structure, links, block IDs, counts, and source coverage.
6. Advance translation to validated only when Step 5 passes.
7. Produce claim-evidence analysis. Never start this step before translation structure validation.
8. Build the knowledge map and incrementally update reusable public notes.
9. Add minimal runnable mechanism code when `code_level` permits, and execute tests before claiming verification.
10. Add concise, dated modern context in its separate note.

## 5. Stage B — one-question learning loop

1. Read the MOC goal, focus, level, progress, and prior learning evidence.
2. Select the smallest coherent next knowledge block.
3. Explain only what is needed for the next attempt.
4. Ask exactly one retrieval, derivation, implementation, or transfer question.
5. Wait for the learner's response.
6. Diagnose the specific gap from the response.
7. Repair only that gap and request a retry.
8. Record the attempt, diagnosis, repair, retry, and evidence.
9. Mark mastery only after a successful explanation, derivation, implementation, debugging task, or transfer.

## 6. Stage C — explicit full-reproduction gate

Enter only for `goal=reproduce` or `code_level=完整复现`. Verify official code provenance, data availability and licensing, preprocessing, environment, hyperparameters, randomness, commands, hardware/cost, metrics, and comparison protocol before running. Distinguish full, partial, failed, and blocked results.

## 7. Output-mode routes

| `output_mode` | Route |
|---|---|
| `混合` | Complete the Stage A reference checkpoint needed for the focus, then alternate with Stage B |
| `仅参考稿` | Complete Stage A; omit mastery claims unless the learner separately attempts checks |
| `仅互动学习` | Initialize and bind a minimal evidence map, then use Stage B; defer full bilingual production without calling it complete |

Time limits reduce scope, never evidence standards. Prioritize the source map, the focused bilingual sections, their analysis, and one learning loop; record deferred sections explicitly.

## 8. Failure states and transitions

| Condition | Status action |
|---|---|
| Initialized only | Keep components `not-started`; initialization proves no paper processing |
| Work begun but incomplete | Mark the relevant component in progress or partial and record the next checkpoint |
| Full text unavailable | Mark source blocked; stop full translation |
| Extraction/OCR uncertainty | Keep the affected page or structure item unvalidated; do not guess |
| Translation validation fails | Keep analysis blocked and list findings |
| Code has not run this turn | Keep code `not-run` |
| Learner has only read or planned | Keep learning not mastered |
| Required checks pass | Advance only the checked component; do not promote unrelated stages |

Persist checkpoint evidence in the manifest, MOC Properties, and the relevant note without overwriting manual content.
