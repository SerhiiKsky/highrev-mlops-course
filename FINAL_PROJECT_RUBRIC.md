# Final Project Rubric

**Scoring:** 100 project points per student, plus optional individual activity points as described below  
**Demonstration:** 15 minutes, live, from the team's repository  
**Written report:** none required

The seven dimensions below sum to 100. Each dimension combines the team result with each student's own evidence: 80% of its points come from the shared project; 20% come from that student's GitHub story and demonstration. This lets students on one team earn different scores while using the same criteria.

Every listed criterion is required for the team result. Score it at its listed weight only when all its acceptance conditions and required evidence are present; otherwise award zero for that criterion. Optional enhancements cannot replace a required criterion or add points beyond 100. Lab checklists are supporting evidence, never separate grades.


## Grading formula

For each dimension `j`, let `Wj` be its weight, `Tj` be the fraction of available team points earned in that dimension, and `Ij` be this student's individual-evidence score: 0 (no usable evidence), 0.5 (either traceable contribution or clear explanation, but not both), or 1 (both). The student's project score is:

`P_student = Σ Wj × (0.8 × Tj + 0.2 × Ij)`

The shared team score `Tj` uses the full criteria and evidence in each dimension. Individual evidence `Ij` is based on the completed rubric form and the student's five-minute part of the final demonstration. The instructor checks links to the student's issues, pull requests, commits, tests, and other relevant artifacts. Commit count and lines of code do not earn points.

Each student's activity points are optional and tracked individually. Approximately 25 raw activity points convert to at most 15 percentage points, at 0.6 grade points per point. The final grade is `min(100, P_student + min(0.6 × A_student, 15))`. A student can receive full project points without activity points.

!!!!
- Homework, lab completion, and checklist completion are not separately graded. 
- The instructor states each live task and its reward during the lesson.

!!!!

The existing project rule for using only the default HighRev data remains: the project score `P_student` is capped at 80/100 before activity points are added. Other projects use the full 100-point rubric.

## Dimension weights

| Dimension | Weight |
|---|---:|
| Environment, data, and run reproducibility | 10 |
| Modular code, tests, and engineering quality | 20 |
| Pipelines and data lineage | 20 |
| Experiment and model lifecycle | 14 |
| API, container, and deployment | 13 |
| CI/CD quality gates | 13 |
| Monitoring, incident diagnosis, and retraining | 10 |
| **Total** | **100** |

## 1. Environment, data, and run reproducibility — 10 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| Locked environment | 1 | A clean checkout resolves and installs the committed environment without manual dependency edits. Python version and dependencies are pinned consistently. | `pyproject.toml`, `uv.lock`, `.python-version`; clean-environment `uv sync --frozen` output in demo or CI. |
| Data identity and restoration | 3 | The raw training data version is addressable from Git and can be restored by a teammate from the configured DVC remote. The data license/source is recorded. | DVC pointer and remote setup instructions; successful `dvc pull` or `dvc checkout`; source/license note. Do not expose credentials. |
| Reproducible run | 2 | A documented command runs the pipeline from versioned data to a named model and metrics without manual notebook execution or unrecorded file copying. | README run command; terminal or CI run; output metrics and model artifact. |
| Run identity | 2 | A model run can be traced to a repository commit, data version, environment, and relevant parameters. | MLflow run or equivalent tracking record with commit and DVC identity tags, parameters, metrics, and artifact reference. |
| Operational instructions | 2 | A new team member can identify prerequisites, configure secrets/remotes safely, and reproduce the main run from the repository README. | Repository README; demonstrate one clean start-to-run path. |

## 2. Modular code, tests, and engineering quality — 20 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| Module boundaries | 4 | Critical-path logic is organized into importable modules with explicit responsibilities; file access and orchestration are separated from transformation/model functions. | `src/` tree; point to one transformation and its caller in the pipeline. |
| Interfaces and maintainability | 2 | Core functions have clear inputs/outputs, useful names, and type/docstring information sufficient for another teammate to use them. | Source inspection during demonstration. |
| Behavioral unit tests | 4 | Tests assert meaningful outputs and include at least one boundary case for a critical transformation or decision. | Focused pytest output and test source. |
| Regression protection | 3 | A deliberate behavior-changing refactor, including a silent prediction/feature change, is caught by an automated test. | Demonstrate or show a recorded test failure after an injected defect, then restored passing result. |
| Integration tests | 3 | At least one automated test exercises a boundary between components, such as pipeline stages, data contracts, or the prediction API. | Test source and passing pytest/CI output. |
| Error handling | 3 | Expected failure scenarios are handled consistently, with actionable error messages. Unsupported edge cases are documented and reflect intentional design limitations rather than omitted required functionality. | Demonstrate one invalid-input or unavailable-dependency scenario; show error response/log and relevant test/documentation. |
| Static quality checks | 1 | The agreed linter/formatter checks pass on project code. | `ruff check` output or CI job. |

## 3. Pipelines and data lineage — 20 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| End-to-end pipeline | 6 | One documented command runs raw/versioned input through preparation and training/evaluation to expected outputs, without manual step ordering. | Kedro pipeline source and successful `kedro run` output. |
| Inspectable graph | 4 | Pipeline nodes and dependencies are named and inspectable; datasets are registered in the catalog. | Kedro pipeline/catalog files and DAG view or equivalent. |
| Configuration separation | 3 | Tunable parameters and dataset locations are configuration, not buried in node implementation. | `conf/` files and a demonstrated parameter change without source edit. |
| Node contracts | 3 | Pipeline nodes use explicit inputs/outputs and do not embed file paths or hidden global state. | Inspect one node and its catalog/config entry. |
| Lineage outputs | 4 | Important intermediate datasets and final outputs are named, persisted or reproducibly generated, and traceable to the run that produced them. | Catalog, output paths, and matching run/artifact references. |

## 4. Experiment and model lifecycle — 14 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| Comparable experiments | 3 | Runs record parameters, metrics, artifacts, and enough identity to compare candidates fairly on the same evaluation protocol. | MLflow experiment with at least two comparable runs; show metric and parameter records. |
| Model registry and versions | 3 | A trained candidate is versioned in a registry or equivalent, with artifact lineage to its run. | Registry view/CLI and the linked run/artifact. |
| Quality gate | 4 | An explicit, problem-justified gate evaluates an absolute quality requirement and/or a justified comparison rule before promotion. Failure reasons are recorded. | Gate implementation/configuration and one passing plus one rejected candidate decision. |
| Promotion state | 2 | Serving resolves a named promoted version/alias; a rejected candidate cannot silently replace it. | Registry alias/version and gate output; demonstrate or show rejection preserving the current promoted version. |
| Reproducible inference artifact | 2 | The registered model includes preprocessing needed for inference, so training and serving do not maintain diverging copies of feature logic. | Artifact signature/input example and raw-input prediction path. |

## 5. API, container, and deployment — 13 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| Prediction contract | 2 | The service defines typed request/response schemas and documents valid inputs and outputs. | OpenAPI/docs and a successful example request. |
| Input validation and service errors | 2 | Invalid requests produce stable, actionable client errors; service/model failures are not returned as misleading successful predictions. | Invalid request demonstration and contract test. |
| Container build | 3 | A documented image build uses the locked runtime dependencies, excludes unnecessary data/secrets, and runs with a least-privilege user or documented equivalent. | Dockerfile, `.dockerignore`, build output/image inspection. |
| Deployment path | 2 | A documented local deployment starts the service and dependencies and serves a health check plus a prediction. | Compose or selected deployment manifests; `health` and prediction output. |
| Orchestration artifact | 2 | Provide either Kubernetes manifests for the service/training job or a Kubeflow Pipelines v2 pipeline that compiles and maps its steps to the training pipeline. A full cluster install is not required. | Apply manifests to a local cluster or show successful KFP v2 compilation plus generated YAML and step mapping. |
| Model version at runtime | 1 | The running service reports or otherwise identifies the model version it serves, and deployment uses the promoted artifact as designed. | Health response/logs and registry reference. |
| Operational failure behavior | 1 | A missing model/registry or unavailable dependency leads to a clear unhealthy/error state and recovery instructions. | Demonstrate or show test/log evidence for one failed startup/dependency case and recovery. |

## 6. CI/CD quality gates — 13 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| Automated validation | 5 | A GitHub Actions workflow runs lint, tests, a pipeline/smoke check, and the model quality gate on the agreed pull-request or push event. | Workflow file and successful run on the team repository. |
| Blocking failure | 3 | A failing required check prevents the release/deployment path; failure reason is visible. | Deliberately failing CI or recorded failed run and branch protection/check configuration. |
| Release artifact | 3 | The release workflow builds and publishes or packages a versioned serving image/artifact tied to a source revision. | Workflow file and tagged release run/image tag. |
| Safe configuration | 2 | Credentials are supplied through repository/environment secrets; workflows avoid printing them and have documented non-secret setup. | Workflow/config inspection and secret names/setup instructions; never expose values. |

## 7. Monitoring, incident diagnosis, and retraining — 10 points

| Criterion | Weight | Mandatory acceptance criteria | Required evidence |
|---|---:|---|---|
| Service and schema health | 2 | The project checks service readiness and input/schema validity before scoring; invalid schema is surfaced rather than silently scored. | Health endpoint/probe and schema failure test or demonstration. |
| Drift evidence | 2 | The system generates a reproducible data/prediction drift report for a defined batch or window. | Batch input, report artifact, and command/configuration that generated it. |
| Outcome quality | 2 | When labels are available, model quality is evaluated separately from input drift, with metric and comparison baseline stated. | Scored batch and quality report/metrics file. |
| Retraining decision | 2 | A deterministic rule states whether to retrain, wait, investigate, or roll back; its output records which signals fired and why. | Decision code/config and `retrain_signal` or equivalent output for at least one incident. |
| Incident diagnosis and failure response | 2 | In the demonstration, the team diagnoses an injected or recorded incident, explains the limitation of the observed signals, and names a safe next action. | 15-minute demonstration plus corresponding report/log/test. |

## GitHub development story and individual rubric form

The project repository should tell a clear story of how the system was built: issues or tasks identify work; commits explain meaningful changes; pull requests connect changes to tests, reviews, and decisions. There is no minimum commit count and no credit for commit volume.

Each student fills in one copy of the table below in the team's repository (for example, `evidence/rubric-<student>.md`). Link the relevant GitHub issue, pull request, commit, test, CI run, or report for each dimension. This form is the contribution record; it is not a separate written report.

| Dimension | Weight | Team evidence / team points | My role and related issue, PR, or commit | Test, CI, or report link | Individual evidence (0 / 0.5 / 1) |
|---|---:|---|---|---|---|
| Environment, data, and run reproducibility | 10 |  |  |  |  |
| Modular code, tests, and engineering quality | 20 |  |  |  |  |
| Pipelines and data lineage | 20 |  |  |  |  |
| Experiment and model lifecycle | 14 |  |  |  |  |
| API, container, and deployment | 13 |  |  |  |  |
| CI/CD quality gates | 13 |  |  |  |  |
| Monitoring, incident diagnosis, and retraining | 10 |  |  |  |  |

## Required final-project evidence and demonstration

- One repository per team of three, based on the instructor-maintained reference baseline.
- Repository code, configuration, tests, tracked reports, and CI runs provide evidence. Completed lab checklists may help reviewers find evidence but carry no separate points.
- No separate written report is required. Maintain a useful operational README as one of the scored project artifacts.
- The final demonstration is 15 minutes: each student has five minutes to present their contribution and how it fits the full system. Show the lifecycle in one connected story: identify code/data/environment, run the pipeline, show experiment and gate, run CI, serve a prediction, show the orchestration artifact, and explain an incident, error handling, and the retraining decision.
- The assessor asks each student about their linked contribution, how it was verified, and one failure case. This helps establish the individual-evidence score.
- Evidence that cannot be run live may be shown from committed CI runs or reports, with the team explaining why it is not live.

## Optional enhancements

Examples include a Streamlit client, an AutoML comparison, CML pull-request reporting, cloud-hosted storage/registry, additional observability, or stronger supply-chain attestations. These earn no points by themselves and do not replace mandatory evidence. They may support a weighted criterion when they provide stronger evidence for that criterion.

The session-12 orchestration criterion is mandatory, with a compile-only Kubeflow Pipelines path so a full cluster is not needed. AutoML is an optional project extension and carries no points by itself.


## Alignment to the 12 sessions (Just a map of content)

| Session | What it contributes to the project | Final-project status |
|---:|---|---|
| 1. ML lifecycle | Frame the prediction decision and tell the operational story in the final demonstration. | Mandatory context for the project narrative. |
| 2. uv environment | Locked, clean-installable environment and repeatable run. | Mandatory; dimension 1. |
| 3. Modularization and tests | Stable interfaces, regression tests, useful errors. | Mandatory; dimension 2. |
| 4. Kedro pipelines | Reproducible DAG, catalog, and parameters. | Mandatory; dimension 3. |
| 5. DVC | Versioned/restorable raw data. | Mandatory; dimension 1. |
| 6. MLflow | Comparable runs, registry, gate, promotion. | Mandatory; dimension 4. |
| 7. AutoML | Candidate generation and trade-off reasoning. | Taught; optional project extension. |
| 8. FastAPI | Typed prediction contract and validation. | Mandatory; dimension 5. |
| 9. Docker | Repeatable serving image. | Mandatory; dimension 5. |
| 10. GitHub Actions | Automated checks and release gate. | Mandatory; dimension 6. |
| 11. Evidently and retraining | Drift/outcome evidence and defensible retraining decision. | Mandatory; dimension 7. |
| 12. Kubernetes/Kubeflow | Compile a Kubeflow Pipelines v2 definition or show Kubernetes manifests for the training/service deployment. | Mandatory; dimension 5. A full managed cluster is not required. |
