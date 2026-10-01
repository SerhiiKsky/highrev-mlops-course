# The Final Project

The project is free in what it predicts and fixed in how it is built. The problem, the data,
the model, and the quality it reaches are the student's choices and the student's
responsibility. The engineering around them is not negotiable: every component in the table
below has to exist, work, and be demonstrated on the student's own repository.

HighRev, the T-shirt shop in this repository, is the dataset the labs are demonstrated on. It
is a teaching example, not the assignment. A project built on HighRev is accepted, with a
lower ceiling on the grade (see Grading).

## What Is Fixed

Each component is taught in one session and has to be present in the final repository. The
right-hand column is what counts as proof during the demonstration.

| # | Required component | Session | Proof |
|---|---|---|---|
| 1 | Reproducible environment: `pyproject.toml`, `uv.lock`, `.python-version` | 2 | `uv sync --frozen` on a clean clone, then the tests pass |
| 2 | Modular code under `src/` with unit and integration tests, lint clean | 3 | `uv run ruff check .` and `uv run pytest` pass; a deliberately injected bug is caught |
| 3 | A Kedro pipeline with a data catalog and a parameters file | 4 | `uv run kedro run` from raw data to a trained model with no manual steps |
| 4 | Raw data versioned with DVC and stored in a remote | 5 | an old commit plus `dvc checkout` reproduces an old model |
| 5 | MLflow tracking, a model registry, a champion alias, and a quality gate | 6 | two runs; the gate promotes one and refuses the other, with the reason logged |
| 6 | A prediction service with a typed request and response contract | 8 | `POST /predict` with raw fields; the schema is published at `/docs` |
| 7 | A container image that carries no model and reads the champion from the registry | 9 | `docker compose up` serves predictions; a new champion needs no rebuild |
| 8 | CI on every push: lint, tests, pipeline, quality gate; a release workflow for the image | 10 | a green run on the student's repository; a red one where the gate failed |
| 9 | Monitoring: data drift and outcome quality kept apart, with a written retraining decision | 11 | an injected shift is detected; the decision names which signal justified it |
| 10 | Kubernetes manifests or a Kubeflow pipeline for the training job | 12 | manifests apply, or the KFP pipeline compiles and its steps match the Kedro pipeline |
| 11 | A README that tells the operational story of the repository | all | a reader can run the whole loop from the README alone |

Everything else from the labs (Streamlit client, AutoML comparison, CML reports, a cloud
remote) is optional. Optional work counts where it strengthens a graded dimension; it does
not substitute for a required component.

## What Is Free

- **The problem.** Any prediction a real person or system would act on. Classification,
  regression, ranking, forecasting, anomaly detection: all fine. The proposal has to say who
  acts on the prediction and what they do differently because of it.
- **The data.** The student's choice, within the rules below.
- **The model.** Any family, any library that fits in the environment. A logistic regression
  that is reproducible, served, and monitored outgrades a gradient-boosted ensemble that is
  not. Model quality is not graded. The choice of metric, the threshold in the quality gate,
  and the argument for both are.
- **Features, preprocessing, AutoML.** Open. The one constraint is architectural: the model
  artifact owns its preprocessing, so the service never re-implements feature logic.
- **The interface.** The API is required; anything in front of it (a Streamlit page, a
  dashboard, a batch job) is the student's call.
- **Where it runs.** Local Compose is enough. A cloud remote for DVC, a hosted MLflow, or a
  managed cluster are welcome and change nothing in the rubric.

## Data Rules

An own dataset is the expected path. It has to satisfy all of the following:

1. **Tabular, with a target.** Rows, columns, and a column to predict. Text or images are
   allowed only as features already reduced to a table.
2. **Large enough to split and to shift.** A working guideline is at least 5K rows. The
   data has to support a train/test split, a holdout the monitoring lab can treat as "new
   production data", and a plausible way to inject or observe drift. A time column makes
   that easy; a natural segment (region, product, cohort) also works.
3. **Small enough to move.** Raw data under 100 MB so DVC with a local or free remote and a
   CI run that trains the model in minutes both stay practical.
4. **Shareable.** Public under a license that permits redistribution, or the student's own
   data with the right to share it with the instructor. No data about identifiable people
   without an explicit license that allows this use.
5. **Not already solved in the repository.** Any dataset other than HighRev.

Sources that meet these rules without much searching: OpenML, the UCI repository, Kaggle
datasets with a permissive license, national open-data portals, and data the student
collects or scrapes with permission.

Projects on the default HighRev data skip the business-understanding and data-understanding
work the rest of the class does, and the grade reflects it: the maximum is 80 of 100.

## Timeline

| By | Deliverable |
|---|---|
| Session 3 deadline | `PROPOSAL.md` in the student's repository (template below) |
| Every session | The session's lab applied to the student's own project, committed and tagged `session-NN-done` |
| Session 6 | A registered model and a quality gate on the student's data |
| Session 10 | CI green on the student's repository |
| Session 12 | Live demonstration |

Labs are demonstrated in class on HighRev. The homework for each session is the same step
on the student's project. A student who only follows along on HighRev has done the lab, not
the homework.

### Proposal Template

Create `PROPOSAL.md` at the root of the repository with these headings. One or two
paragraphs each is enough; a page in total.

```
# Proposal: <project name>

## Problem
What is predicted, who acts on the prediction, and what they do differently.

## Data
Source, license, size, target column, and how the data was obtained.

## Metric and gate
The metric the quality gate will use and why it fits the decision above.
A first guess at the threshold.

## Drift
What a shift in this data would look like in practice, and how it will be
simulated or observed in session 11.

## Risks
What could stop this project, and the fallback.
```

The proposal is a commitment, not a contract. Changing the dataset after session 5 means
redoing the DVC and MLflow work on the new data; that is allowed, and the reason goes into
the README.

## Grading

| Dimension | Weight | Full marks look like |
|---|---:|---|
| Reproducibility of environment, data, and run | 20 | A clean machine rebuilds the environment, pulls the data, and reproduces a named model version from a commit hash |
| Modular code, tests, engineering quality | 15 | Pure functions with tests that catch an injected bug; lint clean; no notebooks on the critical path |
| Pipeline and data lineage | 15 | One command runs raw to model; the catalog shows where every dataset lives; parameters are not in code |
| Experiment and model lifecycle (registry, gate) | 15 | Runs are comparable; the champion is named; the gate's two rules are justified for this problem |
| API, container, deployment | 15 | Typed contract; image without a model; Compose brings up registry and service together |
| CI/CD quality gates | 10 | Lint, tests, and the gate run on push; a failing gate blocks the release |
| Monitoring, incident diagnosis, retraining reasoning | 10 | Drift and outcome quality reported separately; the retrain decision cites the right one |

A project on the default HighRev data is capped at 80 points in total.

Model quality has no row. A proposal that says why a 0.72 AUC is good enough for the decision
it supports, and a gate that enforces it, earns the lifecycle points. A 0.95 with no argument
for the threshold does not.

## The Demonstration

Fifteen minutes, live, on the student's repository and CI. The story runs in this order:

1. New data arrives. Version it with DVC and commit the pointer.
2. Run the pipeline. Show the run in MLflow and the gate's decision.
3. Push. Show CI run the same checks and build the image.
4. Serve. Call the API with raw fields and get a prediction.
5. Inject a shift. Show the monitoring report and the retraining decision.
6. Answer the course question for the prediction on screen: which code, environment, data,
   parameters, model, image, deployment, and monitoring evidence produced it.

Anything that cannot be shown live can be shown as a recorded CI run or a committed report,
with a sentence on why.
