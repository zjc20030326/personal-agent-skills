# Analysis contract

## Evidence layers

Label every substantive record as one of:

- **Author statement:** a claim, definition, result, limitation, or interpretation explicitly made by the paper.
- **Assistant inference:** a reasoned interpretation not explicitly stated by the authors.
- **Later evidence:** post-publication work, current implementations, or modern context, stored outside the original-paper layer with source and retrieval date.

Never paraphrase an assistant inference as an author conclusion. Keep later evidence in `06-后续发展.md` rather than mixing it into the original paper analysis.

## Required analysis

1. **Background and problem:** define the research setting, prior limitation, target problem, and why it matters.
2. **Paper type:** identify the primary and secondary type and justify the classification with sections.
3. **Author claims:** list each claimed contribution in the authors' scope.
4. **Claim-evidence map:** connect every major claim to its theoretical, experimental, systems, qualitative, or dataset evidence.
5. **Method:** record inputs, outputs, representations, modules, objective, training/inference path, and end-to-end data flow.
6. **Evaluation:** record datasets, splits, preprocessing, baselines, metrics, ablations, statistical treatment, compute, latency, memory, and cost when applicable.
7. **Supported result scope:** state exactly which tasks, datasets, settings, seeds, hardware, populations, or assumptions the evidence supports.
8. **Innovations:** distinguish new components, new combinations, new evidence, and new framing.
9. **Assumptions and limitations:** cover explicit limitations plus clearly labeled inferred constraints.
10. **Reproducibility:** assess source/code/data availability, procedural detail, environment specificity, randomness, and missing dependencies.

## Claim-evidence record

Use one record per important judgment:

```markdown
### Claim C3

- Layer: Author statement
- Claim: Concise restatement within the author's scope.
- Evidence: [[6-Results#^s6-p4-en|§6-P4]], Figure 3, Table 2.
- Evidence type: Controlled comparison and ablation.
- Supported scope: Named tasks, datasets, metrics, and run conditions only.
- Caveat: Unmeasured settings or confounds.
- Assistant inference: Separately labeled interpretation, if needed.
```

Do not copy long passages into analysis. Link to the bilingual source block and identify the paper section, paragraph, equation, figure, table, or appendix.

## Method and data flow

Trace the method as a checkable chain:

`input → preprocessing → representation → core operation → objective/output → evaluation`

For each transition, identify shapes/types, learned versus fixed components, training-only versus inference-only behavior, assumptions, and failure modes. Link formulas to their original equation IDs and explanations to the corresponding bilingual blocks.

## Results and scope discipline

- Preserve metric definitions, direction, units, denominator, aggregation, uncertainty, and comparison protocol.
- Distinguish headline results from ablations, sensitivity checks, and negative results.
- Do not claim significance, robustness, efficiency, causality, fairness, or generalization unless the paper's evidence directly supports it.
- Treat missing baselines, compute details, seeds, confidence intervals, or domain coverage as reproducibility limitations, not invented values.
- Compare paper claims with actual evidence before calling an item an innovation or improvement.

## Completion gate

Call analysis complete only when every important judgment has an evidence link, author statements and assistant inferences are separated, result scope is bounded, and limitations/reproducibility are explicit. A polished narrative without these links remains unvalidated analysis.
