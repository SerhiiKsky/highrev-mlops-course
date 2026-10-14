# The Final Project

## TLDR;
You are free to choose what your ML system predicts and which real-world problem it solves.

One restriction: your dataset must be real. No synthetic or artificially generated datasets. Prefer publicly available, real-world datasets that reflect realistic conditions, including noise, missing values, imbalances, or other real-world complexities. Your data should represent a genuine problem, not an artificially simplified classroom example.

What is flexible: The problem, domain, dataset, prediction target, and modeling approach.

What is fixed: The MLOps engineering requirements and grading criteria. Every team must demonstrate a reproducible, tested, versioned, deployable, and monitorable ML system, following the lifecycle covered throughout the course.

You will be evaluated primarily on how reliably you engineer and operate your ML system, not simply how accurate your predictions are.

The goal is not to build the best model. The goal is to build a system that someone else can reproduce, understand, deploy, and maintain.

## Organisation
Each team chooses a problem, data, and model. The engineering components below are built in the team's
private project repository, which is separate from the public course repository, and are
demonstrated at the end of the course.

Homework is separate individual research and preparation. It is ungraded, stays outside the
team project repository, and is not project evidence. The project repository contains the
team's final project work and each student's rubric evidence form.

HighRev, the T-shirt shop in this repository, is the dataset the labs are demonstrated on. It
is a teaching example. Teams may use it for the project; the project-score cap for using only
the default HighRev data is stated in [FINAL_PROJECT_RUBRIC.md](FINAL_PROJECT_RUBRIC.md).
That rubric is the only source for grading details.

## What Is Fixed

Each required component is taught in one session and has to be present in the team's final
repository. AutoML is an optional extension. The rubric defines the acceptance criteria and
evidence for every scored component.

| # | Required component | Session |
|---|---|---|
| 1 | Reproducible environment: `pyproject.toml`, `uv.lock`, `.python-version` | 2 |
| 2 | Modular code under `src/`, tests, and linting | 3 |
| 3 | Kedro pipeline, catalog, and parameters | 4 |
| 4 | Raw data versioned with DVC and stored in a remote | 5 |
| 5 | MLflow tracking, model registry, promoted version, and quality gate | 6 |
| 6 | Optional AutoML candidate evaluation under a fair protocol | 7 |
| 7 | Prediction service with a typed request/response contract | 8 |
| 8 | Docker container and local deployment | 9 |
| 9 | GitHub Actions quality checks and release workflow | 10 |
| 10 | Monitoring and a reasoned retraining decision | 11 |
| 11 | Kubernetes manifests or a Kubeflow Pipelines v2 pipeline | 12 |
| 12 | Operational README | All |

Lab checklists and homework are ungraded. Optional extensions do not replace required
components. See the rubric for which extensions are optional and how evidence is assessed.

## What Is Free

- **The problem.** Any prediction a real person or system would act on. Classification,
  regression, ranking, forecasting, anomaly detection: all fine. Make the decision the model
  supports clear in the team's repository README.
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
5. **Project choice.** Teams should choose data that fits their problem. The default HighRev
   dataset may be used; the rubric states the applicable project-score cap.

Sources that meet these rules without much searching: OpenML, the UCI repository, Kaggle
datasets with a permissive license, national open-data portals, and data the student
collects or scrapes with permission.

Record the source and license so the team can share its data with the instructor. See the
rubric for scoring treatment of the default HighRev dataset.

## Suggested project milestones

Use these milestones to plan team work. They are not separate graded submissions.

| Session | Suggested progress |
|---:|---|
| 3 | Agree a prediction problem and identify candidate data. |
| 6 | Track runs and register a model for the selected data. |
| 10 | Run the quality checks in team-repository CI. |
| 12 | Present the operational system using the final rubric. |

Homework is ungraded research and preparation for concepts discussed in class. The optional
planning prompts below can help a team prepare; no `PROPOSAL.md` submission or separate
written report is required.

### Optional planning prompts

Teams may use these questions while selecting a project:

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

If the team changes its dataset after session 5, repeat the relevant DVC and MLflow work and
briefly explain the change in the operational README.

## Grading

[FINAL_PROJECT_RUBRIC.md](FINAL_PROJECT_RUBRIC.md) is the single source for rubric weights,
acceptance criteria, evidence, individual scoring, activity-point conversion, the HighRev
project-score cap, and the final demonstration. Do not use this project overview or session
checklists as a separate grading scheme.

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
