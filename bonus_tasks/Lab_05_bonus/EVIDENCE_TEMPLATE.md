# Pizza Panic — my completed experiment

Replace every bracketed prompt. Keep this report outside the project during
experiments. Attach screenshots/logs rather than pasting long transcripts here.

## 1. Identity and data versioning

| Field | My evidence |
| --- | --- |
| Student ID / assigned dataset A–E | [fill in] |
| Submitted repository or bundle | [location] |
| Exact Git commit SHA | [fill in] |
| DVC directory hash: `outs[0].md5` | [fill in, including `.dir`] |
| SHA256 of `orders.csv` | [fill in] |
| SHA256 of `restaurants.csv` | [fill in] |
| DVC push and clean Git/DVC evidence | [attachment] |
| Parent search run ID / final status | [fill in] |

Git identifies [explanation]. DVC identifies [explanation]. Raw files live in
[cache/remote explanation], while MLflow stores [explanation].

## 2. My Kedro integration

| Function | My node name | My input names, including parameters | My output names |
| --- | --- | --- | --- |
| `prepare_features` | [fill] | [fill] | [fill] |
| `split_data` | [fill] | [fill] | [fill] |
| `search_candidates` | [fill] | [fill] | [fill] |

- Registry change: [file and explanation].
- Catalog types and paths: [mapping or source reference].
- Configuration environment and MLflow `kedro.env` tag: [fill in].
- Adapter execution call: [my completed line].
- Graph or execution-log attachment: [location].
- Which values live only in memory, and which survive execution? [answer]
- How do YAML settings reach the training function? [answer]
- How does `conf/pizza/` relate to `conf/base/`, and how is it selected? [answer]

## 3. Candidate search

Use child run IDs. Keep full precision in the exported comparison CSV; this
table may round values for readability.

| C | Threshold | Child run ID | Status | Validation ROC AUC | Validation F1 |
| ---: | ---: | --- | --- | ---: | ---: |
| 0.05 | 0.20 | [fill] | [fill] | [fill] | [fill] |
| 0.05 | 0.35 | [fill] | [fill] | [fill] | [fill] |
| 0.05 | 0.50 | [fill] | [fill] | [fill] | [fill] |
| 0.05 | 0.65 | [fill] | [fill] | [fill] | [fill] |
| 0.05 | 0.80 | [fill] | [fill] | [fill] | [fill] |
| 0.5 | 0.20 | [fill] | [fill] | [fill] | [fill] |
| 0.5 | 0.35 | [fill] | [fill] | [fill] | [fill] |
| 0.5 | 0.50 | [fill] | [fill] | [fill] | [fill] |
| 0.5 | 0.65 | [fill] | [fill] | [fill] | [fill] |
| 0.5 | 0.80 | [fill] | [fill] | [fill] | [fill] |
| 5.0 | 0.20 | [fill] | [fill] | [fill] | [fill] |
| 5.0 | 0.35 | [fill] | [fill] | [fill] | [fill] |
| 5.0 | 0.50 | [fill] | [fill] | [fill] | [fill] |
| 5.0 | 0.65 | [fill] | [fill] | [fill] | [fill] |
| 5.0 | 0.80 | [fill] | [fill] | [fill] | [fill] |

Scatterplot: [attachment]. MLflow screenshot/export: [attachment].

**My observation:** [Describe a pattern using at least two specific candidates.
What changes, what stays fixed, and why does the pattern occur?]

**My interpretation:** [Why is the highest ROC AUC not automatically the best
warning policy? Which partition supplied the metrics? Why exclude the test set?]

## 4. My recommendation

- Selected C and threshold: [fill in].
- Original selected child run ID: [fill in].
- Validation ROC AUC / F1 / precision / recall: [fill in].
- Compared with candidate [C, threshold], I recommend this choice because
  [use measurements and explain missed deliveries versus false warnings].
- Apply this policy using the fitted model's probability and [threshold rule].
- This conclusion is limited by [validation/synthetic-data limitation].

## 5. Fresh-clone recovery

Attach a transcript showing the fresh clone without raw CSVs, remote setup,
`dvc pull`, hashes and tracked reproduction command.

- Recovery transcript: [attachment].
- Exact command with my selected settings: [fill in].
- Recovered parent ID / child ID / final status: [fill in].

| Check | Original candidate | Recovered candidate | Match? |
| --- | --- | --- | --- |
| Git commit | [fill] | [fill] | [fill] |
| DVC hash | [fill] | [fill] | [fill] |
| Both CSV hashes | [fill/reference section 1] | [fill] | [fill] |
| C and threshold | [fill] | [fill] | [fill] |
| Split seed, split fractions, max_iter | [fill] | [fill] | [fill] |
| val_roc_auc | [full precision] | [full precision] | [absolute difference] |
| val_f1 | [full precision] | [full precision] | [absolute difference] |
| val_precision | [full precision] | [full precision] | [absolute difference] |
| val_recall | [full precision] | [full precision] | [absolute difference] |
| val_predicted_late | [fill] | [fill] | [fill] |

Tolerance: `1e-8` in the locked environment. Investigate larger discrepancies;
do not round them away.

Why are run IDs different even when the selected experiment matches? [answer]

Why did Git cloning alone not restore the CSVs? [answer]
