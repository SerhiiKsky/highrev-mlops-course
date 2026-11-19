# Lab 07 - AutoGluon to a deployed API

## Incident and goal

A model works locally, but consumers cannot reliably call or update it. In this individual, ungraded lab, train a small AutoGluon candidate using the validated Lab 06 comparison, expose its probability through FastAPI, build a Docker image, and use GitHub Actions to check, publish and request deployment of that exact image to Render. You will verify a prediction and identify the model and source revision. The [final project rubric](../FINAL_PROJECT_RUBRIC.md) governs project grading; this checklist is not graded.

## Before class

You need your own working Lab 05/06 exercise repository and a completed Lab 06 comparison directory. It contains `comparison/protocol.json`, `comparison/membership.csv`, and `comparison/training-input/{fit,holdout,validation}.csv`. Use the **original, unmodified export** from your own completed comparison. It came from your existing Kedro preparation graph and Lab 06 checks, not the `data/05_model_input/train.parquet` path in the old draft. Keep the rest of your project, Kedro graph, DVC pointers, tests and Lab 06 registry records. The Lab 06 final test was already available for a prior decision: its reuse cannot provide an unbiased final audit for this new candidate. A future audit needs fresh untouched data.

Install Git, the GitHub CLI (`gh`), uv, Python 3.11 and 3.12, and Docker with a running daemon. You need a private GitHub repository where Actions and GHCR publishing are enabled and access to a Render account to do the hosted route. This classroom workflow optionally uses approved private copies of the raw CSVs in GitHub, so it does not require a DVC remote on the runner. You must have permission to store the data and model there; otherwise use an approved private data and artifact store and adapt the workflow before running it. Render free resources may be insufficient for this model; see troubleshooting. No cloud credentials or held-out test files belong in Git.

In Bash on Linux/macOS, WSL, or Git Bash on Windows, replace the following three paths with your own absolute paths. Use a **separate exercise checkout**, not the course checkout or the team project. Git Bash users: Docker Desktop must be running and its drive must be shared. Keep the actual paths for later terminals.

```bash
set -euo pipefail
course='/path/to/highrev-mlops-course'
project='/path/to/your-exercise-project'
run='/path/to/your-lab06-run'
test -f "$project/pyproject.toml"
test -f "$project/data/01_raw/customers.csv"
test -f "$run/comparison/protocol.json"
test -f "$run/comparison/membership.csv"
test -f "$run/comparison/training-input/fit.csv"
test -f "$run/comparison/training-input/holdout.csv"
test -f "$run/comparison/training-input/validation.csv"
docker version
uv --version
gh --version
```

Every check must succeed before proceeding. [Starter assets](07_autogluon/README.md) list the supplied files. The lab adds a `lab07` directory; it does not replace or refactor your existing pipeline.

```bash
cd "$project"
test ! -e lab07 || { echo 'lab07 already exists: preserve it and choose a new exercise checkout.' >&2; exit 1; }
cp -R "$course/sessions/07_autogluon/starter" lab07
cd lab07
# The supplied lock requires package-index access for a fresh installation.
uv sync --locked --python 3.11
uv run --locked python -m pytest tests -q
```

One prediction test should initially fail because the API has a student TODO. Other results are not automatically acceptable: read unexpected failures. Keep and commit the supplied `uv.lock`; training and serving use it and the same Linux Python 3.11 image. This lock has been used to build the instructor's Linux training image; a fresh student installation remains to be rehearsed. If installation fails, keep the error and use the instructor fallback; do not change the Lab 05 environment to work around it.

The supplied `lab07` code, like Lab 06's, is not written to your Session 3 Ruff settings. Lab 06 preparation already added `"lab07"` to `extend-exclude` (with `force-exclude = true`) and `lab07/.venv/` to `.gitignore`; check both with `grep -n -A2 'extend-exclude' pyproject.toml` and `git check-ignore -v lab07/.venv` before your first Lab 07 commit, and add them now if they are missing.

## Concepts

For an optional standalone introduction before this applied exercise, see the
[AutoGluon 101 notebook](07_autogluon/01_autogluon_basics.ipynb) and its
[setup guide](07_autogluon/AUTOGLUON_101_SETUP.md). It uses a different toy
dataset and a separate working directory; it is not a substitute for the Lab 06
comparison or the HighRev deployment below.

A **partition** controls what the candidate may see: fit data trains it, holdout data selects among its options, and validation data evaluates the selected candidate. A **model artifact** is the saved predictor and metadata. **FastAPI** validates JSON and loads the artifact once at startup; the request contains already prepared features, not raw customer/order records. Historical features such as `pages_visited` may not be available when predicting a future customer. This API does not establish a valid future-revenue product.

A **container image** packages the application, locked environment and model. An image tag based on a commit identifies the build, while the model version identifies the artifact. GitHub Actions runs checks and publishes the image; Render runs it as a web service. The deploy hook accepts a request asynchronously, so an accepted hook is not proof of a running service. The full final project needs additional quality gates and lifecycle evidence beyond this lab.

## L07-E1 - Preserve and check the existing project

From the project root, activate its own locked environment and run the checks you already use. These example commands assume the Lab 05 project layout and dependencies; if yours differ, use the documented equivalent without deleting tests or checks.

```bash
cd "$project"
uv sync --locked
uv run --locked ruff check src tests
uv run --locked pytest tests -q
uv run --locked kedro run
cd "$project/lab06/worker-env"
uv sync --locked --python 3.11
uv run --locked python -m unittest discover -s ../tests -v
cd "$project"
```

All must pass. Record your project commit (`git rev-parse HEAD`), data version (`cat data/01_raw.dvc`), and Lab 06 protocol ID from `comparison/protocol.json`. Confirm the raw inputs match their DVC pointer and the Lab 06 comparison was created successfully with the original membership and provenance checks. Stop if inputs, lock, or project state have changed since the comparison; create a new Lab 06 comparison instead of editing its records. Do not repeat its consumed audit or replace the pipeline with the AutoGluon script.

**Checkpoint:** working Kedro pipeline and prior project and Lab 06 checks; retained original Lab 06 comparison and input identity. Reopen a terminal by redefining the three paths above. Failure: inspect the first failed command and restore the missing environment/data using the previous lab instructions; rerun before continuing.

## L07-E2 - Train and evaluate an AutoGluon candidate

The training image uses a small random forest with AutoGluon, a bounded search budget and the original customer-disjoint fit and holdout partitions. It checks the protocol and membership hashes, verifies partition row IDs and labels and checks customer separation. It does **not** independently prove every feature value still matches the original export: use the unmodified Lab 06 files and retain their provenance. No test feature file is read.

Build the training image from your new `lab07` directory. In Git Bash, `cygpath -m` converts mount paths for Docker Desktop; on Linux/macOS/WSL use absolute POSIX paths.

```bash
cd "$project/lab07"
docker build -f Dockerfile.train -t highrev-lab07-train .
comparison_host=$(cd "$run/comparison" && pwd -P)
output_host=$(pwd -P)
if command -v cygpath >/dev/null 2>&1; then
  comparison_host=$(cygpath -m "$comparison_host")
  output_host=$(cygpath -m "$output_host")
fi
test ! -e model || { echo 'model already exists: preserve it before another run.' >&2; exit 1; }
MSYS_NO_PATHCONV=1 docker run --rm \
  --mount "type=bind,source=$comparison_host,target=/input,readonly" \
  --mount "type=bind,source=$output_host,target=/output" \
  highrev-lab07-train --comparison /input --output /output/model --version lab07-v1
cat model/lab07-model.json
```

Record validation ROC AUC, artifact size, p95 prediction time, batch size, protocol ID and the Lab 06 baseline results. Compare only when dataset, metric, batching and measurement environment match; ten timings on a small batch are a classroom estimate, not a service latency guarantee. Explain one deployment trade-off. The time limit is a training budget, not a strict deadline.

**Checkpoint:** `model/` contains a reloadable predictor and `lab07-model.json`. If training fails, retain the output and logs, inspect the first error, then choose a fresh exercise location or move the failed output to a new safe location before retrying. Do not overwrite an earlier artifact. The model may encode training data even after cached tables are removed; only publish it when its data and artifact are approved for the intended audience.

## L07-E3 - Complete and test the API; build the image

Open `lab07/lab07/api.py` in your exercise project. In the TODO, call the loaded predictor's `predict_proba(frame)` and return the probability for positive class label `1` as a Python float. The saved predictor owns its feature preprocessing. The tests use a fake predictor to check the API contract; they do not prove the actual artifact loads.

```bash
cd "$project/lab07"
uv run --locked python -m pytest tests -q
docker build --build-arg SOURCE_REVISION=local -t highrev-lab07-api .
docker run --rm -p 127.0.0.1:8007:10000 highrev-lab07-api
```

Keep the server running. In a **second terminal**, test it; adjust the port if 8007 is occupied:

```bash
curl --fail-with-body http://127.0.0.1:8007/health
curl --fail-with-body http://127.0.0.1:8007/predict \
  -H 'Content-Type: application/json' \
  -d '{"pages_visited":3,"age_first_order":30,"gender":"F","campaign":true,"ip_address_country":"PL","browser":"Chrome","os":"Windows"}'
```

Open `http://127.0.0.1:8007/docs`. Health should report ready, `lab07-v1`, and `local`; the prediction should include a probability between 0 and 1 and the same model version. Add an extra `high_revenue` field to the request and check that the API rejects it with 422. Stop the container with Ctrl+C in the first terminal. If startup fails, read the container logs and verify the artifact exists and was trained with the same lock and Linux/Python environment; a missing model must not produce a ready response.

**Checkpoint:** keep the model, API change, lock, test results, and successful local request. Keep raw data and secrets out of the image; raw data may enter the private exercise repository only with permission as described in E4.

## L07-E4 - Publish and deploy the checked image

The workflow runs existing project checks and Kedro, verifies model input provenance, runs API tests, builds and exercises the image, publishes a commit-tagged image, and then requests deployment. The workflow does not retrain the model, prove its quality, or replace the Lab 06 promotion gate. A copied artifact is a classroom selection, not an MLflow promotion.

1. For the optional classroom route, first confirm that the data owner permits copies of the two raw CSV files in your **private** exercise repository. The runner cannot access the Lab 05 local-only DVC remote. With permission, prepare separate copies without moving the originals or overwriting existing files:

   ```bash
   cd "$project"
   mkdir -p ci-data
   for name in customers.csv orders.csv; do
     test -f "data/01_raw/$name"
     test ! -e "ci-data/$name" || { echo "ci-data/$name already exists; preserve and inspect it." >&2; exit 1; }
     cp "data/01_raw/$name" "ci-data/$name"
   done
   touch .gitattributes
   grep -Fqx 'ci-data/*.csv -text' .gitattributes || printf '\n%s\n' 'ci-data/*.csv -text' >> .gitattributes
   ```

   The `.gitattributes` rule preserves the CSV bytes when Git checks them out on another operating system; changing line endings would change their hashes. Check the copies with `cmp data/01_raw/customers.csv ci-data/customers.csv` and the equivalent command for `orders.csv`. The workflow copies these approved files into `data/01_raw/` on the runner, then checks the model's recorded input hashes. Retain the DVC pointer and all existing local data checks: this copy method does **not** prove restoration from a DVC remote. Keep `.dvc/config.local` and credentials out of Git.
2. Run `uv run --locked python lab07/lab07/verify_provenance.py` from the project root. It compares the restored raw-file and project-lock hashes with the Lab 06 provenance recorded in the model. A mismatch stops release; investigate and make a new Lab 06 comparison and model if necessary. This identity check is not proof of model quality or a full lineage attestation.
3. Confirm you are permitted to store the trained artifact in this repository and image. Inspect its contents and privacy requirements: `save_space` removes cached tables but cannot guarantee the model reveals no training information. Use a private repository and private GHCR package unless the data owner approves public release. Ensure `lab07/model/` is available in the GitHub checkout; for this classroom route, commit the approved model files, using `git check-ignore -v lab07/model/lab07-model.json` to inspect ignore rules and `git add -f lab07/model` only if needed. Commit the approved `ci-data/` copies and `.gitattributes` for this route; do not commit the DVC-managed `data/01_raw/` originals, Lab 06 run directory, virtual environments, or secrets. For sensitive/large artifacts use an approved private artifact store instead, and adapt the workflow to restore it.
4. Copy the workflow into a **new** file without replacing any existing workflow:

```bash
cd "$project"
mkdir -p .github/workflows
test ! -e .github/workflows/lab07.yml || { echo 'Existing workflow: inspect and merge manually.' >&2; exit 1; }
cp "$course/sessions/07_autogluon/workflow/lab07.yml" .github/workflows/lab07.yml
git status --short
```

Review, commit, and push your own code, lock, approved model and workflow to the exercise repository. The default release branch in this example is `main`; adjust both branch conditions if yours differs. Watch the Actions run: all prior checks, provenance check, API tests and image smoke test must pass. The first run can publish without a Render hook; note its image `ghcr.io/OWNER/REPOSITORY:COMMIT_SHA` in lowercase.
5. In Render, create a **Web Service -> Existing Image** using that exact GHCR image. For a private package, configure a Render registry credential with a GitHub token allowed to read that package (`read:packages`). Select a compute plan; configure `/health` as the health check. The application listens on `0.0.0.0:$PORT`. Confirm startup and call `/health` and `/predict` on the provided HTTPS URL. Never paste a token into the repository or logs.
6. Copy the service's secret deploy hook. From your project root, the following Bash command stores it as a repository Actions secret without echoing it or putting its value in shell history:

```bash
set +x
read -rs -p 'Paste the Render deploy hook: ' render_hook
printf '\n'
if [ -n "$render_hook" ]; then
  if printf '%s' "$render_hook" | gh secret set RENDER_DEPLOY_HOOK; then
    echo 'Secret saved.'
  else
    echo 'Secret was not saved; stop and diagnose before pushing.' >&2
  fi
else
  echo 'No hook entered; nothing was saved.' >&2
fi
unset render_hook
```

   Alternatively, store it as a secret in the GitHub `render` environment. If both exist, the environment secret takes precedence; make sure it is current. Make a small safe change, commit and push it to `main`. The workflow supplies that commit's image tag through Render's `imgURL` parameter. The image repository must match the service's configured image repository. Inspect the Render deploy status, then call health and predict. Confirm `source_revision` equals the **new** GitHub commit SHA and `model_version` is your selected version. A hook response means accepted or queued, not healthy. Manual Render deploys may return to the service's configured default tag.

**Checkpoint:** keep the workflow run link, image tag, Render deployment status and redacted health/prediction results. For a failed check, inspect the first failing job; the image/deploy jobs are blocked by required validation. If GHCR rejects a push, inspect the package's Settings → Manage Actions access: a package can be linked to the correct repository yet still need the workflow repository to have write access. Keep the package private and don't delete it to reset permissions. For a failed deployment, check registry access, image name/tag, logs, memory and health. If Render is unavailable or the free plan runs out of memory, retain the passing local container and CI evidence; the hosted path remains unverified, not passed. Do not expose the secret hook URL while troubleshooting.

## Expected results and troubleshooting

| Check | Expected observation | What it does not prove |
|---|---|---|
| E1 previous checks | Existing tests and Kedro pass on restored data | Cloud deployment or candidate quality |
| E2 candidate | Report includes AUC, size, timing and protocol ID | Fresh unbiased final test or production latency |
| E3 API | Valid prediction; invalid request rejected; missing model prevents startup | That a remote service is running |
| E4 release | Tests and image smoke pass; GHCR image tag equals source SHA | Hook acceptance alone does not prove a healthy deployment |
| E4 Render | Public health and real prediction with expected model/source identifiers | Monitoring, authentication, or production readiness |

Free Render web services have limited memory and CPU, sleep when idle, and have ephemeral writable storage. A warm-up can be slow. The model is inside the image, not saved only to a running container's filesystem. If resource limits prevent startup, use an approved higher-memory plan or instructor demonstration; do not silently claim success.

## Exit checklist and next step

- [ ] I preserved and ran the existing project checks and Kedro pipeline.
- [ ] I used the Lab 06 customer-disjoint partitions and did not use test features for selection.
- [ ] I explained validation quality, model size and latency limits.
- [ ] I implemented and tested the API and verified the local container.
- [ ] I identified the source revision, model version and how the release is blocked when checks fail.
- [ ] I recorded a live Render result or the exact blocker and local fallback.

Keep your work in your individual exercise repository. Next, Lab 08 watches this model for data and prediction drift: it adds Evidently to the project environment and compares new data with the data the model was trained on. The serving contract, deployment tests and promotion relationship return in later labs. Optional individual research: investigate an input-schema change, memory exhaustion, a failed check, and model drift. Explain which are visible to deployment checks and which need monitoring.

References: [AutoGluon deployment](https://auto.gluon.ai/stable/tutorials/tabular/advanced/tabular-deployment.html), [Render image deployment](https://render.com/docs/deploying-an-image), [Render deploy hooks](https://render.com/docs/deploy-hooks), [Render free-service limits](https://render.com/docs/free), [GitHub image publishing](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images).
