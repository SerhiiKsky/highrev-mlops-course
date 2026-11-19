# Session 08 notes — monitoring and retraining

Copy this file to `notes/session-08.md` in your exercise project. These are your
own observations; they are not graded.

## Model and data

- Model version (from `lab07/model/lab07-model.json`):
- Lab 06 run directory used (`$run`):
- Commit the incident ladder ran on (`git rev-parse --short HEAD`):

## Incident table

Fill "Predicted" in L08-E1, the rest in L08-E5 from days 6–10. Taxonomy rows:
input distribution, label distribution, schema, feature–label relationship,
upstream source, upstream model.

| Incident | What the simulator changes | Taxonomy row | Predicted layer (B / C / both / neither) | Layer B observed | Layer C observed (ROC AUC days 6–10) | Action in the signal | Correct action, and why |
|---|---|---|---|---|---|---|---|
| none | | | | | | | |
| schema | | | | | | | |
| covariate | | | | | | | |
| concept | | | | | | | |
| category (optional) | | | | | | | |
| new_category (optional) | | | | | | | |
| corrupt (optional) | | | | | | | |

Taxonomy rows this simulator cannot produce, and how you would notice them:

## L08-E2 threshold decision

- Column that drifted on every clean day, and its distance:
- Threshold chosen, and why it still catches a real shift:
- Why this column is an open domain and `os` is not:

## L08-E3 observation

- Range of ROC AUC over the clean stream:
- Why accuracy is not used for the decision:

## L08-E4 test I added

- What it checks and which mistake it would catch:

## L08-E5 concept stream day by day

| Decided until | Hard | Parametric | IQR | Action |
|---|---|---|---|---|
| 2026-10-06 | | | | |
| 2026-10-07 | | | | |
| 2026-10-08 | | | | |
| 2026-10-10 (default) | | | | |

Why the relative tests go quiet:

## My retraining rule

- Retrain when:
- Investigate, without retraining, when:
- False alarm or missed incident this rule accepts:
- Who decides promotion after retraining, and with which evidence:
