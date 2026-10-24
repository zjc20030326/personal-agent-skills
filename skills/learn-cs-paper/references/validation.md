# Validation contract

## Skill and encoding checks

Decode every Markdown and YAML file as strict UTF-8. Require `SKILL.md` frontmatter to contain only `name` and `description`, a trigger-only description under 500 characters, and a body under 500 lines. Resolve all eight direct reference links and require no deeper reference chain.

Run the official validator:

```powershell
$env:PYTHONUTF8='1'
python 'C:\Users\m1881\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'C:\Users\m1881\.agents\skills\learn-cs-paper'
```

Scan non-template files for unfinished authoring markers and unrendered double-brace tokens. Template renderer tokens are permitted only under `assets/templates/`.

## Script checks

```powershell
python -m py_compile 'C:\Users\m1881\.agents\skills\learn-cs-paper\scripts\workspace_contract.py' 'C:\Users\m1881\.agents\skills\learn-cs-paper\scripts\init-paper-workspace.py' 'C:\Users\m1881\.agents\skills\learn-cs-paper\scripts\validate-paper-workspace.py'
python -m unittest discover -s 'C:\Users\m1881\.agents\skills\learn-cs-paper\tests' -v
```

The baseline at this revision is 68 tests: expect 67 passes plus at most the permission-specific Windows symlink skip, with zero failures and zero errors. If hardening adds tests, use the newly discovered total and require every added test to pass; do not treat this baseline as a cap. A skip for any other reason requires investigation.

## Workspace CLIs

Initialize:

```text
python scripts/init-paper-workspace.py --vault VAULT --collection COLLECTION --title TITLE [--source SOURCE] [--source-pdf PDF] [--doi DOI] [--arxiv ARXIV] [--year YEAR] [--skill-version VERSION] [--json]
```

Validate without modifying:

```text
python scripts/validate-paper-workspace.py WORKSPACE [--vault VAULT] [--json]
```

Validator exit/status contract:

| Exit | Status | Meaning |
|---|---|---|
| 0 | `ok` | No error findings |
| 1 | `invalid` | Workspace loaded, but one or more validation findings are errors |
| 2 | `error` | Invocation, Vault, workspace, or manifest loading failed |

## Validation categories

Check all independent categories; do not suppress later checks after one loaded-workspace finding:

- required path existence/kind and exactly one root titled MOC;
- manifest schema, skill/version, title, workspace-root, source, PDF-path, and hash ownership invariants shared with initializer resume;
- strict UTF-8 Markdown loading;
- unrendered template markers;
- unique Obsidian block IDs, including IDs attached to paragraph ends;
- one-to-one `-en`/`-zh` block-ID pairing inside `02-双语对照`, without applying that suffix rule to other notes;
- resolvable local Wikilinks/embeds and Markdown links inside the declared Vault, including strict heading/block-anchor checks in linked public notes, while ignoring valid literal/code and external targets;
- manifest list/count and required-path-count consistency;
- copied-PDF existence, workspace containment, and lowercase SHA-256 match.
- manifest/MOC synchronization for translation, analysis, and learning progress, plus rejection of stale `initialized` status after work begins.

Representative finding codes include `invalid-manifest-ownership`, `missing-path`, `wrong-path-kind`, `duplicate-moc`, `markdown-read-error`, `duplicate-block-id`, `unpaired-bilingual-block-id`, `unresolved-wikilink`, `unresolved-heading-anchor`, `unresolved-block-anchor`, `checkpoint-mismatch`, `manifest-count-mismatch`, `invalid-manifest-structure`, `missing-pdf`, `pdf-outside-workspace`, and `pdf-hash-mismatch`. Loading codes include `invalid-arguments`, `invalid-workspace`, `missing-manifest`, `invalid-manifest`, `invalid-vault`, and `workspace-load-failed`.

## Honest completion states

- Initialized means only that the safe workspace skeleton and manifest exist.
- Translation complete requires ordered coverage and translation-structure validation.
- Analysis complete requires traceable claim-evidence judgments after the translation gate.
- Mastered requires a successful learner retry or transfer task.
- Code verified requires direct current-turn execution.
- Full reproduction requires the complete declared pipeline and documented metric comparison.

Never promote an unrelated stage because another stage passed.

## First Attention smoke test

In a temporary Vault, initialize **Attention Is All You Need** with a small local PDF fixture, DOI/arXiv metadata, and JSON output. Validate the reported workspace, inspect the dynamic titled MOC, 11 required paths, copied PDF/hash, manifest, and safe same-hash re-run.

This smoke test proves initializer/validator behavior only. It does not prove that the paper was translated, analyzed, learned, that attention code ran, or that the paper was reproduced. Full paper evidence belongs to the later real trial.
