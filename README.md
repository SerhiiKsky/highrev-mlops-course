# HighRev MLOps Course

One project, twelve sessions. A T-shirt shop wants to know which customers will become
high-revenue. The model that answers that question starts here as a single script and ends
the course as a versioned, tested, tracked, containerized, monitored service with a
retraining decision behind it. Every session removes one production risk from this
repository.

This is the **starter** commit. It holds only what session 1 needs. The rest arrives one
session at a time.

## How This Repository Works

The repository is public and grows on a schedule. Nothing is posted ahead of the session
that teaches it.

- **`main`** gets one commit per session, posted the week the session is taught, tagged
  `session-NN`. A drop only adds files: the session brief under `sessions/`, data under
  `data/`, and fixtures or checks under `checks/`. It never edits a file a student owns, so
  pulling it never conflicts with student work. Anything the student must change, such as a
  dependency or a parameter, is an instruction in the brief, not a diff in the drop. A drop
  never contains the solution.
- **`main` is append-only.** Corrections to a posted brief arrive as new commits, never as
  rewritten history, so every student copy can keep pulling.
- **Solutions are not in this repository.** A reference implementation for each session is
  shared separately after that session's deadline. Nothing a student can pull from here will
  ever overwrite their own code.

### Student Setup

Student work lives in a **private copy**, not a fork. A fork of a public repository is
public on GitHub, which would make every student's homework readable by every other student.

1. Create an empty **private** repository on GitHub named `highrev-mlops-course`. Do not add
   a README or `.gitignore`; it must be empty.
2. Clone the course repository, point `origin` at the private copy, and keep the course as
   `upstream`:

   ```bash
   git clone https://github.com/<course-org>/highrev-mlops-course.git
   cd highrev-mlops-course
   git remote rename origin upstream
   git remote add origin https://github.com/<student>/highrev-mlops-course.git
   git push -u origin main --tags
   ```

   GitHub's **Import repository** page does the same thing in the browser; after importing,
   add `upstream` by hand with the third command above.
3. Invite the instructor as a collaborator: repository **Settings**, **Collaborators**,
   **Add people**, GitHub handle `<instructor-github-handle>`. Review happens on commits in
   the private copy, so without this invitation there is nothing to grade.

Then, each week:

```bash
git pull upstream main --tags
```

Files under `sessions/`, `data/`, and `checks/` belong to the course; leave them unchanged.
Student code goes in `src/`, `tests/`, and the configuration files each session asks for.
The student creates those; the course never writes into them.

### Submitting A Session

The commit history is the submission. For each session:

- Commit as the work progresses, with messages that say what changed and why. One commit
  that says "session 3" is one commit's worth of evidence; ten that each name a decision are
  ten.
- When the session's checklist is done, tag the last commit and push:

  ```bash
  git tag session-03-done
  git push origin main --tags
  ```

- The review covers every commit between the previous `-done` tag and this one, against the
  checklist at the end of the brief. Comments arrive on the commits in GitHub; replies and
  fixes are further commits, not amended ones.

A session submitted after its deadline is still reviewed; the delay is noted in the grade,
and the next session's work still has to start from it.

## Session 1 Setup

The baseline is one script with three third-party dependencies. Install them any way that
works and run it:

```bash
pip install pandas scikit-learn user-agents
python baseline.py
```

Expected output, give or take the last digit:

```
ROC AUC  0.764
accuracy 0.721
f1       0.302
saved model.pickle
```

If it fails, or the numbers differ, write down the Python and package versions and bring them
to session 2. That difference is the first incident of the course.

## What Is Here, And What Is Not

The full project this course builds is laid out below. The starter has the first two rows.

| Piece | In the starter | Arrives in | Replaces |
|---|---|---|---|
| `data/01_raw/*.csv` | yes, committed to Git | session 5 moves it to DVC | data that only exists on one laptop |
| `baseline.py` | yes, one script | session 3 splits it into `src/highrev/` | notebook code nobody can test |
| `pyproject.toml`, `uv.lock`, `.python-version` | no | session 2 | `pip install` and hope |
| `tests/unit`, `tests/integration`, ruff | no | session 3 | "nothing crashed, so it's fine" |
| `conf/base/catalog.yml`, `parameters.yml`, Kedro pipelines | no | session 4 | hard-coded paths and constants |
| `data/01_raw.dvc`, `.dvc/` | no | session 5 | 3 MB of CSV in every commit |
| `src/highrev/tracking.py`, MLflow registry, champion alias, quality gate | no | session 6 | metrics printed to a terminal |
| AutoML protocol (PyCaret, AutoGluon) | no | session 7 | one hand-tuned model |
| `src/highrev/serving/api.py`, `ui.py` | no | session 8 | a pickle and a Slack message |
| `Dockerfile`, `compose.yaml` | no | session 9 | "works on my machine" |
| `.github/workflows/` | no | session 10 | manual testing before release |
| `src/highrev/monitoring/`, Evidently reports, retrain signal | no | session 11 | finding out from the business |
| `k8s/`, `kubeflow/` | no | session 12 | one server, one team |

## Syllabus

Each session opens with an incident and fixes it on this project. Briefs appear in
`sessions/` as they are posted.

| # | Session | Incident | Brief |
|---|---|---|---|
| 1 | Lifecycle and system thinking | "The script runs. The score is fine. Now what?" | [posted](sessions/01-introduction.md) |
| 2 | Reproducible environment | "Works on Alice's laptop, fails on Bob's." | week 2 |
| 3 | Modularization and tests | "A refactor changed predictions without an exception." | week 3 |
| 4 | Pipelines with Kedro | "Nobody knows which cells run in which order." | week 4 |
| 5 | Data versioning with DVC | "The commit exists; the training CSV does not." | week 5 |
| 6 | Experiment tracking and registry with MLflow | "Thirty-seven runs. Which one is in production?" | week 6 |
| 7 | AutoML | "The best model is too slow and too large to serve." | week 7 |
| 8 | Serving with FastAPI | "A backend engineer asks for the prediction contract." | week 8 |
| 9 | Docker | "The endpoint works locally, not on the host." | week 9 |
| 10 | CI/CD with GitHub Actions | "A bad model passed unit tests and was deployed." | week 10 |
| 11 | Monitoring and retraining | "Inputs drifted. Should we retrain?" | week 11 |
| 12 | Kubernetes and Kubeflow | "Ten teams need isolated, repeatable training jobs." | week 12 |

## Grading

The final project is this repository, in the student's private copy, demonstrated end to
end: new
data arrives, it is versioned, the pipeline runs, the run is tracked, the gate decides, CI
passes, an image is built, the model is served, a shift is injected, it is detected, and a
retraining decision is made and defended.

| Dimension | Weight |
|---|---:|
| Reproducibility of environment, data, and run | 20 |
| Modular code, tests, engineering quality | 15 |
| Pipeline and data lineage | 15 |
| Experiment and model lifecycle (registry, gate) | 15 |
| API, container, deployment | 15 |
| CI/CD quality gates | 10 |
| Monitoring, incident diagnosis, retraining reasoning | 10 |

The model's score is not a row in that table. A 0.76 AUC that can be reproduced, served, and
monitored beats a 0.94 AUC that lives in one notebook.

## Conventions

- Python 3.12 from session 2 on. Windows, macOS, and Linux are all supported; commands are
  shown for a POSIX shell and work in Git Bash on Windows.
- Questions about a session go to the course repository's issues, titled with the session
  number. Fixes to course files arrive through the weekly drop.
- Decks and readings from the earlier ASI course are referenced by module number in each
  brief; they are not part of this repository.
