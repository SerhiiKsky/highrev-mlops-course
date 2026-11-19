# Session 08 checklist

An ungraded self-check. The [final project rubric](../../FINAL_PROJECT_RUBRIC.md)
governs project grading.

Setup

- [ ] Evidently 0.7.23 and pandas 3.0.6 are in my project lock, and I can say why pandas is pinned.
- [ ] The replaced `verify_provenance.py` passes, and I can explain why the release gate checks the model's recorded lineage rather than today's lock.
- [ ] My earlier project, Kedro and `lab07` tests still pass.

Layers and evidence

- [ ] I can name layers A, B and C and say which needs labels.
- [ ] My drift reference is the data my monitored model was fitted on, and I can say why it is not Kedro's `train_set`.
- [ ] My `check_schema` reports missing, extra, mistyped and unseen-value problems, and treats an open-domain column separately.
- [ ] I chose a threshold for the column that alarmed on clean data and recorded why.
- [ ] My `score_batch` refuses lost or duplicated rows, and every score row carries the model version and commit.
- [ ] I can explain why accuracy stays near 0.9 when ROC AUC falls.

Decision

- [ ] My hard, parametric and IQR tests pass the supplied tests and one test of my own.
- [ ] I ran `schema`, `covariate` and `concept` and compared the results with my predictions.
- [ ] I can say which incident no layer B check can see and which no layer C check can see.
- [ ] I can explain why the relative tests stop firing during a lasting incident.
- [ ] I wrote a retraining rule with its accepted trade-off, and I know that the Lab 06 gate, not the monitor, decides promotion.

Handoff

- [ ] Code, tests, parameters, lock, `.gitignore` and `notes/session-08.md` are committed; streams and reports are not.
