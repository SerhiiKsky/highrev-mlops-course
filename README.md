# HighRev MLOps Course

One project, twelve sessions. A T-shirt shop wants to know which customers will become
high-revenue. The model that answers that question starts here as a single script and ends
the course as a versioned, tested, tracked, containerized, monitored service with a
retraining decision behind it. Every session removes one production risk from this
repository.

This is the **starter** commit. It holds only what session 1 needs: the baseline script, its
data, and a small notebook-to-container walkthrough. The rest arrives one session at a
time.

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
  shared separately after the session. Nothing a student can pull from here will
  ever overwrite their own code.

### Student Setup

Keep two repositories, with separate working folders:

1. Clone this public course repository for lesson briefs, labs, and reference material:

   ```bash
   git clone https://github.com/<course-org>/highrev-mlops-course.git
   cd highrev-mlops-course
   ```

   Update this checkout when course materials change with `git pull --tags`.
2. Create a separate **private** repository for your team project. Clone that repository
   into its own folder and invite all three teammates and the instructor.
3. Follow each brief to create or copy only the named starter code into the team project
   repository. Do not copy the course repository's `.git` history, lesson files, or lab
   checklists into the project repository. Do not add the course repository as a Git remote.

Course materials stay in the course checkout and update there. Teams implement project work
in their private project repository. No course update is merged over team work. Homework is
separate individual research and preparation: keep it outside the team project repository;
it is not collected or graded.

### Showing Your Development Story

Use issues, commits, and pull requests to make the team's engineering story easy to follow.
This history supports the final-project evidence and each student's rubric form; it is not a
separate session grade. Do not optimize for commit count.

- Write commit messages that explain meaningful changes and why they were made. Link pull
  requests to issues or tasks when possible, and include tests/review in the story.
- Session tags are optional checkpoints, not submissions. If your team uses one:

  ```bash
  git tag session-03-done
  git push origin main --tags
  ```

The instructor assesses the final project using [FINAL_PROJECT_RUBRIC.md](FINAL_PROJECT_RUBRIC.md).
Each student fills in the rubric's evidence form with links to their relevant issues, pull
requests, commits, tests, and reports. Lab checklists are ungraded learning aids.

## Session 1 Setup

Two things have to be on the machine before session 1: **Python 3.12** and **Docker**
(Docker Desktop on Windows and macOS, Docker Engine on Linux). `docker run --rm hello-world`
has to work; the brief says what to check if it does not.

In the course checkout, the baseline is one script with three third-party dependencies.
Install them any way that works and run it:

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

The second half of session 1 is a walkthrough from a notebook to a running container on a
toy regression problem. Its files are in [`sessions/01_intro/`](sessions/01_intro/) and the
[brief](sessions/01-introduction.md) has the steps; the walkthrough is done in a copy at
`intro/`, so nothing under `sessions/` is edited.

## What Is Here, And What Is Not

The full project this course builds is laid out below. The starter has the first two rows.

| Piece | In the starter | Arrives in | Replaces |
|---|---|---|---|
| `data/01_raw/*.csv` | yes, committed to Git | session 5 moves it to DVC | data that only exists on one laptop |
| `baseline.py` | yes, one script | session 3 splits it into `src/highrev/` | notebook code nobody can test |
| `sessions/01_intro/`: notebook, `api.py`, `Dockerfile` on a toy regression | yes, as a preview of sessions 8 and 9 | the HighRev versions arrive in sessions 8 and 9 | a pickle only its author can call |
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

Each session opens with an engineering incident and practical work on HighRev. Homework is
ungraded research and preparation for concepts discussed in class. Briefs appear in
`sessions/` as they are posted.

| # | Session | Incident | Brief |
|---|---|---|---|
| 1 | Lifecycle, system thinking, and a first container | "The script runs. The score is fine. Now what?" | [posted](sessions/01-introduction.md) |
| 2 | Reproducible environment | "Works on Alice's laptop, fails on Bob's." | [posted](sessions/02-environment.md) |
| 3 | Modularization and tests | "A refactor changed predictions without an exception." | [brief](sessions/03-modularization-and-tests.md) |
| 4 | Pipelines with Kedro | "Nobody knows which cells run in which order." | week 4 |
| 5 | Data versioning with DVC | "The commit exists; the training CSV does not." | week 5 |
| 6 | Experiment tracking and registry with MLflow | "Thirty-seven runs. Which one is in production?" | week 6 |
| 7 | AutoML | "The best model is too slow and too large to serve." | week 7 |
| 8 | Serving with FastAPI | "A backend engineer asks for the prediction contract." | week 8 |
| 9 | Docker | "The endpoint works locally, not on the host." | week 9 |
| 10 | CI/CD with GitHub Actions | "A bad model passed unit tests and was deployed." | week 10 |
| 11 | Monitoring and retraining | "Inputs drifted. Should we retrain?" | week 11 |
| 12 | Kubernetes and Kubeflow | "Ten teams need isolated, repeatable training jobs." | week 12 |

## The Project and Grading

HighRev is the instructor-maintained reference project. Each team develops its project in
one private repository. [PROJECT.md](PROJECT.md) describes the project scope and required
technical components. [FINAL_PROJECT_RUBRIC.md](FINAL_PROJECT_RUBRIC.md) is the single source
for weights, acceptance criteria, required evidence, individual contribution scoring, activity
points, and the final demonstration. Use its form to link each student's work to the team's
GitHub story. There are no separate homework, lab-checklist, or session grades.

## Conventions

- Python 3.12 throughout: session 1 installs it by hand, session 2 pins it. Docker from
  session 1 on. Windows, macOS, and Linux are all supported; commands are shown for a POSIX
  shell and work in Git Bash on Windows.
- Questions about a session go to the course repository's issues, titled with the session
  number. Fixes to course files arrive through the weekly drop.
- Decks and readings from the earlier ASI course are referenced by module number in each
  brief; they are not part of this repository.
