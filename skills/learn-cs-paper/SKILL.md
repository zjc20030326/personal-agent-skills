---
name: learn-cs-paper
description: Use when a user provides or identifies a computer-science paper and wants to read, translate, understand, learn, explain, implement, reproduce, or turn it into structured Obsidian notes.
---

# Learn CS Paper

## Core principle

Produce a traceable bilingual learning workspace and verified learning evidence, not a long summary. Keep the paper, source-faithful translation, assistant analysis, later research, code execution, and learner mastery as separate evidence layers.

## Start brief

Infer and record these fields before choosing a route:

| Field | Default when safely inferable |
|---|---|
| `source` | Determine from the supplied PDF, Zotero item, DOI, arXiv ID, or paper page |
| `goal` | Understand |
| `focus` | The paper's central contribution |
| `level` | Graduate-entry depth |
| `time_budget` | Unbounded |
| `output_mode` | Mixed |
| `code_level` | Minimal implementation |
| `modern_context` | Concise |
| `vault` | `D:\Markdown\Obsidian\Obsidian-Notes` |
| `collection` | `论文\机器学习` |

Ask only one question when missing information materially changes the route. Otherwise state assumptions in the paper MOC and begin.

In the first response, state that the multi-file MOC workspace is manifest-driven: `assets/paper-manifest.json` binds the selected source, version, SHA-256, stage state, and resumable checkpoints, and drives every later resume.

## Boundary router

| Request | Route |
|---|---|
| General CS concept, book, course, or video without a specific paper | Use `learn-anything-fast` or a future specialist, not this Skill |
| Mathematics paper with proof-oriented learning | Use a future `learn-math-paper` or the mathematics workflow |
| Pure anonymous review, score, or accept/reject judgment | Use `academic-paper-review` |
| Zotero library, metadata, collection, or attachment management | Use the Zotero workflow; never modify Zotero as part of this Skill |
| Computer-science paper learning, bilingual translation, implementation, or reproduction | Use this Skill |

## Source gate

Use lawful full text in this order: user-provided or local PDF, Zotero PDF attachment, arXiv or author-public version, then a DOI page the user can access. Record the source, version, retrieval date, and SHA-256 hash before translation.

When only metadata or an abstract is available, stop full translation. Limit statements to the available evidence and request or locate lawful full text. Never invent missing sections, bypass access controls, or treat an abstract as the paper.

Before full-text bilingual translation, also record the source's license and the rights basis for that use. Full-text translation is allowed only for text/PDF supplied by the user or material whose license or public-domain status permits it; public accessibility alone is not redistribution permission. When that basis is absent, provide a compliant summary with only short necessary excerpts and ask the user to supply the text/PDF. Keep generated full-text outputs private unless redistribution rights are established.

## Stage controller

1. **Stage A — reference workspace:** initialize safely, map the source structure, translate in source order, validate translation structure, then analyze, build knowledge links, add minimal mechanism code, and keep modern context separate.
2. **Stage B — interactive learning:** choose one knowledge block, ask exactly one retrieval, derivation, implementation, or transfer question, wait for the learner, diagnose only the demonstrated gap, repair it, and request a retry before marking mastery.
3. **Stage C — full reproduction:** enter only when `goal=reproduce` or `code_level=完整复现`. Record and execute the complete reproducibility chain; report partial or failed results honestly.

Translation structure validation gates analysis. Reading, planning, note creation, and workspace initialization do not prove mastery or reproduction.

## Resource router

Read only the references whose observable condition is present. Every detailed contract is one hop from this file.

| Reference | Read when |
|---|---|
| [Workflow](references/workflow.md) | Selecting parameters, source/version, output mode, stage transitions, resume behavior, or a failure route |
| [Translation contract](references/translation-contract.md) | Producing or validating bilingual paragraphs, equations, algorithms, figures, tables, appendices, or references |
| [Paper types](references/paper-types.md) | Classifying the paper and adapting evidence or overclaim checks |
| [Analysis contract](references/analysis-contract.md) | Writing background, claim-evidence analysis, method/data-flow analysis, results, innovations, limitations, or reproducibility judgments |
| [Knowledge learning](references/knowledge-learning.md) | Building prerequisite/core/extension maps, updating reusable notes, or running mastery checks |
| [Code reproduction](references/code-reproduction.md) | Implementing a mechanism, testing code, using official repositories, or attempting partial/full reproduction |
| [Obsidian output](references/obsidian-output.md) | Initializing, naming, navigating, or incrementally updating the Vault workspace |
| [Validation](references/validation.md) | Checking the Skill, workspace, manifest, links, hashes, completion claims, or the first smoke test |

## Conditional capabilities

Invoke capabilities only when their condition occurs:

- Use `paper-search`, `arxiv`, or `literature-search-arxiv` for source discovery.
- Use `pdf` or `pdf:pdf` for PDF extraction, inspection, rendering, OCR assessment, and page evidence.
- Use `academic-paper-review` for a strict critique branch, while keeping learning outputs separate.
- Use `math-reasoning` for a difficult derivation.
- Hand a general prerequisite concept to `learn-anything-fast` only when this paper-specific workflow identifies that gap.
- Use `obsidian-markdown` for Obsidian syntax and safe note editing.
- Use the normal execution and testing workflow for actual code verification.

Do not load every capability by default or duplicate its generic instructions here.

## Resume and version safety

Initialize with the bundled script before writing the workspace. Resume a matching PDF hash, isolate a changed hash in a sibling workspace, and refuse to take over a directory without a manifest. Preserve existing Markdown and manual content; never silently merge versions or overwrite public knowledge notes.

## Interaction contract

Ask one question and wait. Accept the learner's attempt before diagnosing. Repair only the missing reasoning step, then ask for a retry or a closely matched transfer. Mark a concept mastered only when the learner supplies evidence through explanation, derivation, implementation, debugging, or transfer.

## Quick reference

| Goal | Minimum route | Completion evidence |
|---|---|---|
| Read or translate | Source gate → Stage A through translation validation | Structure and bilingual links validate |
| Understand or present | Stage A analysis → Stage B | Claim-evidence map plus successful retrieval/transfer |
| Implement | Stage A → minimal mechanism code → Stage B | Current-turn execution and tests |
| Reproduce | Stage A → explicitly gated Stage C | Recorded environment/data/run evidence and honest metric comparison |

## Example route

For **Attention Is All You Need** with focus on tensor shapes, multi-head attention, and positional encoding, infer graduate-entry depth, mixed output, minimal implementation, and concise modern context unless the user says otherwise. Build the faithful bilingual reference workspace first. Implement scaled dot-product attention and multi-head attention with shape assertions and mask tests. Then ask one tensor-shape, derivation, implementation, or transfer question and wait; do not include model answers in advance.

## Common mistakes

| Mistake | Correction |
|---|---|
| Put everything in one huge note | Keep the MOC as the sole entrypoint and link separate evidence layers |
| Mix commentary into translation | Keep translation source-faithful; put interpretation in analysis |
| Analyze before structure validation | Validate the translation structure first |
| Expand an abstract into invented text | Stop at the source gate |
| Ask several questions at once | Ask exactly one and wait |
| Label unrun code verified | Keep it `not-run` until direct execution succeeds |
| Mix current knowledge into the original paper | Put it in the separate modern-context note with dated sources |
| Merge a changed PDF silently | Create an isolated hash-versioned workspace |
