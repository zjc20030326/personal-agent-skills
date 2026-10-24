# Bilingual translation contract

## Source boundary

Translate only text present in a lawful full source. Record the source/version, retrieval date, PDF page, SHA-256 binding, license, and rights basis. Full-text bilingual translation is permitted only for text/PDF supplied by the user or material whose license or public-domain status permits that use. Public accessibility alone does not establish redistribution permission. When the rights basis is absent, provide a compliant summary with only short necessary excerpts and ask the user to supply the text/PDF. Keep full-text translation outputs private unless redistribution rights are established.

When only metadata or an abstract exists, stop full translation. When OCR or reading order is uncertain, preserve the page evidence, label the uncertainty, and do not reconstruct prose by guesswork.

## Ordered inventory

Before translation, enumerate sections, paragraphs, equations, algorithms, figures, tables, appendices, and references in source order. Give every section and paragraph a stable ID and store the lists/counts in the manifest. Use the inventory as the coverage contract.

## Paragraph format

Use stacked blocks, not a two-column Markdown table:

```markdown
**Original · §2.1-P3**

A complete source paragraph occupies this block in its original language. ^s2-1-p3-en

**译文 · §2.1-P3**

这一块保存对应段落的完整中文译文。 ^s2-1-p3-zh
```

Keep the same logical ID in both labels. Use globally unique Obsidian block IDs. Link analysis to the exact block, for example `[[2-Section Name#^s2-1-p3-en|原文 §2.1-P3]]`.

## Translation rules

- Preserve paragraph boundaries and source order. Do not collapse several source paragraphs into a summary.
- Preserve headings, emphasis, footnotes, citations, and cross-references when recoverable.
- Keep technical meaning before stylistic fluency. Record ambiguous readings instead of silently choosing.
- Build a terminology table before sustained translation with English term, chosen Chinese term, first location, alternatives, and rationale.
- Use one chosen translation consistently. At first occurrence, retain the English term when ambiguity matters.
- Keep explanation, critique, implementation notes, and later developments out of the translation layer.
- Keep reference entries in their original language and order; do not translate bibliography entries one by one.

## Equations and algorithms

- Preserve equation and algorithm order, numbering, symbols, cases, and cited definitions.
- Use `$...$` for inline math and `$$...$$` for display math in Markdown.
- Do not replace an equation with prose. Add a faithful Chinese lead-in after the original lead-in when needed.
- If formula extraction is unreliable, retain a page crop and page number, mark the item unvalidated, and defer derivation to analysis.
- Preserve algorithm inputs, outputs, initialization, loops, conditions, and complexity statements.

## Figures and tables

For each item record:

- original number and order;
- English caption;
- Chinese caption;
- PDF page;
- source image or page crop;
- extraction uncertainty.

Treat the original image as authoritative. Create a Markdown table only when cell structure is reliable; otherwise retain the image and a scoped description. Never redraw data without checking values.

## Appendices and references

Preserve appendix order and numbering. Translate appendix prose under the same paragraph contract. Preserve proof, derivation, supplementary experiment, and ablation boundaries. Keep the full references section in the original language and record each entry in the manifest inventory.

## Validation gate

Before analysis, verify:

1. Every inventory item has an output or an explicit uncertainty record.
2. Section and paragraph order matches the source.
3. English/Chinese IDs pair one-to-one.
4. Block IDs are unique and resolvable.
5. Equations, algorithms, figures, tables, appendices, and references retain their numbering/order.
6. Captions and PDF pages are present where required.
7. No commentary or assistant inference appears in the translation layer.

Keep translation partial when any required check fails; do not unlock analysis by assertion alone.
