# Session 05 evidence board

Fill this in with your own observations. A value or run ID is evidence only
when you can say where it came from and what it proves.

## Ex 1 — Find missing evidence

- Pipeline input paths, configured split and model options:
- Produced model and metrics paths:
- Missing evidence for the incident:

## Ex 2 — Version/publish V1

- Pointer path and V1 data hash:
- Git commit containing pointer:
- Remote location (local exercise path, no credentials):
- Did push succeed? How do you know?

## Ex 3 — Restore V1 in independent clone

- Clone path and Git commit:
- Pointer/hash and file checksums in original and clone:
- Evidence of pull without relying on the original cache:
- What this check does and does not prove:

## Ex 4 — Connect MLflow

- What each of the three implemented functions logs:
- A run ID, status, commit, data hash, effective parameters, metrics and artifacts:
- How the effective configuration is obtained:

## Ex 5 — Compare A/B/C

| Run | ID | Commit | Data hash | C | Seed / test size | ROC AUC | Other observations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | | | | | | | |
| B | | | | | | | |
| C | | | | | | | |

- A vs B: what changed, what stayed fixed, and what can we conclude?
- A vs C: what changed, what stayed fixed, and what can we conclude?
- Why are these experiment scores not proof of production readiness?

## Ex 6 — Reproduce a run and inspect failure

- Chosen run ID and its **run** commit (not necessarily the early V1 pointer commit):
- Data hash, effective configuration, environment, and restoration evidence:
- Original metric, reproduced metric, absolute difference, tolerance, and explanation:
- Deliberate failure cause, run ID/status, and recovery:
- Remaining reproduction limitations:

## Exit ticket

1. A commit exists but the raw data are missing. What else is needed?
2. Two AUC scores differ. What records should be compared first?
3. Why do DVC and MLflow not replace Kedro?
