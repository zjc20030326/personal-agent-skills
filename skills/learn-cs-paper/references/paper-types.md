# Paper-type adaptations

Classify the paper before analysis. Use the declared type as a hypothesis until the full paper supports it. A paper may combine types; name the primary type and any secondary lens.

| Paper type | Primary evidence | Analysis emphasis | Common overclaim risk |
|---|---|---|---|
| Model or algorithm | Formal definition, architecture, objective, algorithm, ablations, comparisons | Inputs/outputs, data flow, inductive bias, complexity, optimization, mechanism evidence | Treating benchmark gains as proof of the proposed mechanism or universal superiority |
| Empirical or benchmark | Dataset construction, protocol, baselines, metrics, statistical treatment, error analysis | Fairness of comparisons, leakage, variance, robustness, domain coverage | Generalizing beyond sampled tasks, datasets, seeds, or metric definitions |
| Systems | Architecture, workload, hardware/software environment, latency/throughput/cost, failure behavior | End-to-end bottlenecks, resource tradeoffs, scalability, reliability, reproducibility | Claiming portable gains from one stack, workload, or hardware setting |
| Theory-heavy CS | Definitions, assumptions, theorem statements, proofs, bounds, counterexamples | Assumption necessity, proof structure, asymptotics, constructive implications, links to algorithms | Treating asymptotic or idealized guarantees as measured practical performance |
| Survey | Search scope, taxonomy, inclusion criteria, synthesis method, coverage dates | Taxonomy quality, missing subfields, comparison dimensions, historical framing | Treating the survey's selection as exhaustive or its synthesis as primary experimental evidence |
| HCI or user study | Recruitment, participants, tasks, instruments, protocol, qualitative coding, statistics, ethics | Ecological validity, sampling, confounds, triangulation, participant context | Universalizing findings from a narrow population or lab task |
| Dataset | Collection, consent/license, annotation, splits, quality controls, bias audits, benchmark use | Representativeness, leakage, label validity, governance, downstream limitations | Treating size or benchmark utility as proof of neutrality or broad coverage |
| Application | Domain problem, operational constraints, data provenance, deployment context, domain metrics | Fit to domain needs, safety, distribution shift, workflow integration, external validity | Confusing a case study or retrospective dataset with general clinical/industrial effectiveness |

## Adaptation rules

- Preserve the same translation, traceability, versioning, and evidence boundaries for every type.
- Emphasize the evidence native to the type; do not force every paper into a model-paper template.
- Separate author claims from assistant classification and inference.
- For mixed papers, use multiple rows but avoid double-counting one result as independent evidence.
- Record absent evidence as absent, not as a negative result.

## Exclusion

Do not use this matrix to absorb a mathematics paper whose core task is proof-oriented mathematical learning. Route it to a future `learn-math-paper` or the mathematics workflow. A theory-heavy computer-science paper remains in scope when its questions, models, or computational consequences are fundamentally CS-facing.
