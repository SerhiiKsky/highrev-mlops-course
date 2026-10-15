# Session 03: contracts and evidence

Complete this record in `notes/session-03.md` in your exercise repository. It is an ungraded
working aid. Record observations from your own runs; do not turn predictions into evidence.

## Ex 1 — Map responsibilities and save the baseline

- Starting commit and data identity:
- Python, pandas, scikit-learn, numpy, uv, and Ruff versions:
- Baseline command and observed three metrics / test-row count:
- Script regions that read/write files:
- Script regions that transform data:
- Script regions that split/train/evaluate:
- Dependency changes made for this lesson and any repeat baseline run:

## Ex 2 — Extract modules without changing behavior

| Function | Inputs / preconditions | Output / invariants | Side effects allowed? |
|---|---|---|---|
| prepare_orders | | | |
| prepare_customers | | | |
| label_customers | | | |
| split_data | | | |
| build_model / train_model / evaluate_model | | | |
| runner.main | | | |

- New command's metrics compared with the same locked baseline:
- Differences investigated and their explanations:

## Ex 3 — Specify contracts and write focused tests

| Behavior | Small input | Independently calculated expectation | Test name |
|---|---|---|---|
| Repeated-customer aggregation | | | |
| Fractional age | | | |
| Invalid birthdate repairs | | | |
| Strict age limit and inner join | | | |
| Threshold equality and parameter use | | | |
| Input unchanged | | | |
| Split and preprocessing behavior | | | |

- Focused command / observed outcome:
- What a passing unit suite does not establish:

## Ex 4 — Catch deliberate regressions

| Deliberate edit | Test already present before edit | Observed failure | Restored result |
|---|---|---|---|
| Fractional-age calculation | | | |
| Threshold comparison | | | |

- Why aggregate model scores alone are insufficient:

## Ex 5 — Decide and test invalid-input behavior

- Negative-quantity policy and reason:
- Expected behavior for a mixed valid/invalid customer:
- Expected behavior if all supplied orders are invalid:
- Error type/message requirement, if rejecting:
- Tests changed and normal-input regression result:
- Why this is an intentional behavior change:

## Ex 6 — Integrate the runner and quality checks

- Import side-effect check command / result:
- Integration command / result / artifact location:
- Baseline comparison after all changes:
- Workflow step order and run URL, or explicitly local-only evidence:
- My commit / PR and self-review observations:
- Remaining limitations and Session 4 recovery work:
