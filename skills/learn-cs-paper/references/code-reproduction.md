# Code and reproduction contract

## Default route: minimal runnable mechanism

Default to the smallest runnable code that reveals the paper's core mechanism. Keep it separate from a full model or training pipeline. Include explicit inputs/outputs, shape/type assertions, deterministic fixtures where possible, edge cases, and tests that can fail for the mechanism under study.

For **Attention Is All You Need**, the minimal verified scope includes:

- scaled dot-product attention;
- multi-head attention;
- tensor-shape assertions across batch, head, sequence, and feature dimensions;
- mask tests, including broadcasting and excluded-position behavior.

Do not label architecture-wide training, benchmark reproduction, or paper metrics verified from these mechanism tests.

## Reproduction gate

Enter a full reproduction only when `goal=reproduce` or `code_level=完整复现`. Before execution, record:

1. official/author code URL, revision, license, and correspondence to the paper version;
2. dataset source, license/access, split, preprocessing, filtering, and checksum when available;
3. operating system, hardware, runtime, package environment, and dependency versions;
4. model configuration, initialization, optimizer, schedule, batch construction, stopping rule, and checkpoints;
5. random seeds, nondeterministic operations, repeated runs, and aggregation;
6. exact commands, configuration files, artifacts, logs, and timestamps;
7. paper metrics, local metrics, definitions, denominators, and comparison tolerance;
8. every intentional or unavoidable difference from the paper.

Never bypass access controls or fabricate unavailable data/configuration. Estimate cost before a long training run and obtain any authority the execution environment requires.

## Status labels

Use exactly these code/reproduction labels:

| Status | Meaning |
|---|---|
| `not-run` | Code or commands exist but have not been executed in the current turn |
| `verified-minimal` | The scoped mechanism code ran in the current turn and its relevant assertions/tests passed |
| `partial-reproduction` | A recorded subset of the paper pipeline ran; omitted stages and metric limits are explicit |
| `full-reproduction` | The complete declared pipeline ran and the paper/local comparison is documented |
| `failed` | Execution was attempted and failed; preserve the command, error, environment, and next hypothesis |

Only direct current-turn execution advances status. Old logs, repository badges, prior reports, code inspection, compilation alone, or another person's claim may inform context but do not verify the current run.

## Verification workflow

1. Define the exact scope and expected observable behavior.
2. Inspect source provenance and dependency boundaries.
3. Write or select focused assertions/tests.
4. Execute in the current environment and capture commands plus outputs.
5. Compare actual behavior with the scoped expectation.
6. Update the status and differences only from this evidence.

If execution is unavailable, leave `not-run` and provide a reproducible run plan. If part of the pipeline succeeds, use `partial-reproduction`, not `full-reproduction`.

## Reporting differences

Separate:

- implementation differences;
- data and preprocessing differences;
- environment/hardware differences;
- hyperparameter and randomness differences;
- evaluation-protocol differences;
- observed metric differences;
- unresolved causes.

Do not normalize away a discrepancy. Explain whether it weakens mechanism understanding, result comparability, or the reproduction claim.
