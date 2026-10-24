---
name: writing-mathematical-latex
description: Use when Codex needs to write, edit, or review mathematical LaTeX for a ChatGPT response, a Markdown document, or a pure .tex source file, including proofs, calculations, or formula-heavy explanations.
---

# Mathematical LaTeX Writing

Determine the target artifact before formatting. The channel that carries the answer does not determine the math delimiters. Preserve any explicit project style or user-specified delimiters when they conflict with this skill.

Read [references/math-latex-style.md](references/math-latex-style.md) before producing or substantially revising mathematical content. Use it for the medium-specific delimiter contract, notation, display choices, calculus, linear algebra, derivation detail, and final checks.

## Workflow

1. Resolve the target medium with this strict priority:
   1. If the user requests Markdown, Markdown-ready content, or `.md` content, use the Markdown contract `$...$` and `$$...$$`, even when returning it in chat.
   2. Otherwise, if the user requests a pure `.tex` file, LaTeX fragment, LaTeX source, or content ready to place in `.tex`, use the `.tex` contract `$...$` and `\[...\]` or a suitable LaTeX environment, even when returning it in chat.
   3. Otherwise, for an ordinary conversational explanation of mathematics, use the ChatGPT contract `\(...\)` and `$$...$$`.
2. Check whether an existing document establishes hard local conventions that must be preserved.
3. Preserve mathematical meaning, assumptions, domain restrictions, and symbols before changing typography.
4. Apply the resolved delimiter contract and use semantic LaTeX commands rather than visual approximations.
5. Choose inline math for short expressions integrated with a sentence; use display math for long, central, aligned, matrix, or multi-step content.
6. Make every nontrivial derivation auditable. Show the intermediate transformations that determine an order, coefficient, convergence condition, or final value.
7. Check delimiters, braces, environments, operator limits, differentials, display punctuation, and notation consistency before returning the result.

Minimal routing examples:

- Request: "Write this as Markdown-ready text." Output form: `The value is $x=1$.`
- Request: "Give source that can be placed in a pure .tex file." Output form: `The value is $x=1$.`
- Request: "Explain in this conversation why the value is one." Output form: `The value is \(x=1\).`

## Delivery rules

- Treat Markdown or `.tex` wording in the request as the target-artifact contract; never replace it with the ChatGPT contract merely because the answer is delivered in chat.
- For a Markdown target, emit Markdown-ready source without surrounding math expressions in code ticks.
- For a `.tex` target, emit only LaTeX source appropriate to the surrounding document; do not insert Markdown fences unless requested.
- Use the ChatGPT contract only for ordinary conversational mathematics when the user did not request Markdown or `.tex` output.
- Keep existing user macros and document preambles unless the task asks to change them. If a required command depends on a package or macro not known to be available, state that dependency rather than silently assuming it.
- Do not invent a document template, course-specific structure, numbering scheme, metadata, or domain conventions.
