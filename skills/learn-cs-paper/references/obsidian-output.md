# Obsidian output contract
## Workspace layout

Initialize under `<vault>/<collection>/<sanitized paper title>/`:

```text
<sanitized paper title>/
├── <sanitized paper title> - MOC.md
├── 01-论文地图.md
├── 02-双语对照/
│   ├── 0-Abstract.md
│   ├── 1-First Source Section.md
│   ├── 2-Next Source Section.md
│   └── References.md
├── 03-深度分析.md
├── 04-知识地图.md
├── 05-代码与复现.md
├── 06-后续发展.md
├── 07-互动学习记录.md
└── assets/
    ├── <copied source PDF when supplied>
    ├── paper-manifest.json
    ├── figures/
    └── tables/
```

Generate bilingual filenames dynamically from the paper's actual first-level sections; do not assume the example section names. Preserve source order with a stable numeric prefix. Keep the references file in the original language.

Use `知识库/计算机/机器学习/` for stable public concept notes. Keep paper-specific explanations in the paper workspace.

## MOC Properties and role

The `<sanitized paper title> - MOC.md` file is the sole entrypoint. Keep these Properties current:

```yaml
---
type: cs-paper
title: Paper title
aliases: []
authors: []
year: 0
venue: ""
doi: ""
arxiv: ""
paper_type: unverified
domain: computer-science
source_pdf: ""
status: initialized
focus: []
translation_progress: 0
analysis_progress: 0
learning_status: not-started
created: ISO-8601 timestamp
updated: ISO-8601 timestamp
tags:
  - paper/computer-science
---
```

Use actual metadata instead of the illustrative values. The MOC links metadata/source PDF, manifest, progress, every workspace note, knowledge dependencies, code status, and open questions. Never embed the full translation in the MOC.

## Initializer CLI

Run in UTF-8 mode when the shell encoding is uncertain:

```powershell
$env:PYTHONUTF8='1'
python 'C:\Users\m1881\.agents\skills\learn-cs-paper\scripts\init-paper-workspace.py' --vault 'D:\Markdown\Obsidian\Obsidian-Notes' --collection '论文\机器学习' --title 'Paper Title' --source 'Source reference' --source-pdf 'C:\path\paper.pdf' --doi 'DOI' --arxiv 'arXiv ID' --year 'Year' --json
```

Omit optional flags when unknown. `--skill-version` defaults to the installed canonical version `1.0.0`; pass an explicit canonical SemVer only when testing or migrating another installed release. The manifest records the same nonempty version in both `skill.version` and `skill_version`. Capture the absolute `workspace`, `manifest`, created-path list, and `new_workspace` from JSON output.

## Safe re-run behavior

- Matching manifest and PDF hash resumes without overwriting existing Markdown.
- A changed PDF hash selects a sibling workspace suffixed by the first eight hash characters.
- An existing directory without `assets/paper-manifest.json` is refused.
- Before any resume, the initializer verifies manifest schema, `learn-cs-paper` ownership, sanitized title/root identity, source record invariants, and the copied PDF SHA-256.
- An unequal PDF destination, active lock, unsafe collection, unrelated/inconsistent manifest, or invalid canonical skill version stops the write.
- Manual content always wins. Never rebuild a generated file over user edits.

## Template roles

| Template | Generated role |
|---|---|
| `paper-moc.md` | Sole navigation entrypoint and Properties |
| `paper-map.md` | Source/version and ordered structure inventory |
| `analysis.md` | Author claims, evidence, assistant inference, limitations, reproducibility |
| `concept-note.md` | Paper-local knowledge map and public-note links |
| `study-log.md` | One-question attempts, diagnosis, repair, retry, mastery evidence |

The initializer also creates conservative starting notes for code/reproduction and modern context. Templates provide structure, not completed paper content.

## Incremental updates
1. Read the manifest and current note before every write.
2. Update only the owned section or append a source-labeled section.
3. Preserve user prose, Properties not owned by the workflow, block IDs, Wikilinks, and file names already referenced.
4. Update dates, progress, counts, and validation evidence only after the corresponding action.
5. Record conflicts and uncertainties; do not silently merge versions.
6. Re-run workspace validation after structural changes.
