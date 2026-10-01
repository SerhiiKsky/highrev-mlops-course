# Session 01: Lifecycle And System Thinking

**Incident.** A data scientist hands over `baseline.py`. It reads two CSV files, trains a
model, prints a ROC AUC of 0.76, and saves a pickle. The business wants predictions in the
checkout flow next quarter. Everyone in the room agrees the model is fine. Nobody can say
what happens next.

**Goal.** See the whole lifecycle before touching any tool, then walk one small model
through the part `baseline.py` stops short of: install the libraries, train in a notebook,
save the fitted model, wrap it in a prediction service, pack the service into a Docker
image, and call it over HTTP. Leave with a list of everything that has to be true for a
prediction to be trusted a year from now.

## The Problem

A T-shirt shop sells online. Some customers come back and spend far more than the rest. If
the shop could tell, at a customer's first order, who will become high-revenue, it could
spend its retention budget on them. The target is binary: total spend above 300 is
`high_revenue`.

## The Data

Two files in `data/01_raw/`, committed to Git for now.

`customers.csv`, one row per customer:

| Column | Meaning |
|---|---|
| `customerID` | identifier, joins to `orders.customer_id` |
| `gender` | M or F |
| `birthdate` | `YYYY/M/D`; three rows fall on February 29 of a non-leap year |
| `user_agent` | browser string at sign-up; the script parses browser and OS from it |
| `ip_address` | dropped before modeling |
| `campaign` | whether the customer arrived through a campaign |
| `ip_address_country` | country resolved from the IP |

`orders.csv`, one row per order line:

| Column | Meaning |
|---|---|
| `order_date` | `YYYY/MM/DD` |
| `pages_visited` | pages viewed in the session that produced the order |
| `order_id` | identifier |
| `customer_id` | joins to `customers.customerID` |
| `tshirt_category` | four categories, written two different ways in the raw data |
| `tshirt_price`, `tshirt_quantity` | multiplied to get the line total |

Features used by the baseline: `pages_visited`, `age_first_order`, `gender`, `campaign`,
`ip_address_country`, `browser`, `os`.

## The Lifecycle

CRISP-DM (ASI module 2) describes the loop: business understanding, data understanding,
preparation, modeling, evaluation, deployment. `baseline.py` covers the middle four steps
in 150 lines. The course is about the loop closing: deployment produces new data, new data
changes the model's world, and the model has to be retrained, re-evaluated, and redeployed
without anyone redoing the first five steps by hand.

The question every student should be able to answer by session 12:

> What code, environment, data, parameters, model, image, deployment, and monitoring
> evidence produced the prediction I am looking at right now, and what happens when it
> stops working?

Each noun in that sentence is a session. Today's container covers "model", "image", and
"deployment" in the smallest way that still counts: a prediction another program on the
same machine can ask for. The sessions after this one make that service reproducible,
tested, tracked, and monitored.

## In Class

1. Run `baseline.py`. Note the Python version, the package versions, and the three metrics.
2. Read the script top to bottom. Every `COURSE NOTE` comment marks a production risk. For
   each one, write down in one sentence what goes wrong if it is left as is.
3. In pairs, list what has to be true for a prediction from this model to be trusted in the
   checkout flow in twelve months. Group the list under the nouns in the question above.
4. Compare the group's list with the syllabus in the README. Anything on the list that no
   session covers is worth raising now.
5. Walk through the deployment below. For each step, write down what it produces and what
   the next step consumes.

## First Deployment: Notebook To Container

The walkthrough uses a second, deliberately tiny problem, not HighRev. The diabetes dataset
bundled with scikit-learn has 442 rows, ten numeric features, and a numeric target, so
there is nothing to download, nothing to clean, and nothing to tune; the whole exercise is
the plumbing around the model. It is a regression, so the scores are MAE and R², not ROC
AUC. HighRev stays the course's classification case study and is not touched here. The
target is a measure of disease progression after one year; nothing in this exercise says
anything about medical usefulness.

The course files are in [`01_intro/`](01_intro/):

| File | Role |
|---|---|
| `01_train_and_serve.ipynb` | trains and evaluates the model; saves it, one request, and the expected answer |
| `requirements.txt` | the six libraries the notebook and the service need |
| `api.py` | a FastAPI service that loads the saved model and answers `/health` and `/predict` |
| `Dockerfile` | packs the service, its dependencies, and the model into an image |
| `.dockerignore` | keeps the notebook, the environment, and data out of the image |

Files under `sessions/` belong to the course, so the work happens in a copy at the root of
the repository:

```bash
cp -r sessions/01_intro intro
cd intro
```

Everything below runs inside `intro/`. Commands are for a POSIX shell, which on Windows
means Git Bash; the three places where Windows differs are called out.

### 1. Check Docker

Install Docker Desktop (Windows, macOS) or Docker Engine (Linux), start it, and run:

```bash
docker --version
docker run --rm hello-world
```

The first line prints the client version. The second pulls a small image and starts a
container from it. An **image** is a packaged filesystem plus a startup command; a
**container** is one running instance of an image. If the second command cannot reach the
Docker daemon, the engine is not running yet.

### 2. Create The Environment And Install The Libraries

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows the first two lines are `py -3.12 -m venv .venv` and
`source .venv/Scripts/activate`.

Read `requirements.txt` first. pandas holds tables, scikit-learn supplies the dataset and
the model, joblib saves the fitted pipeline, FastAPI and Uvicorn serve HTTP, and JupyterLab
runs the notebook. Installing them makes them importable in this environment and nothing
more; no model exists yet.

### 3. Train In The Notebook

```bash
python -m jupyter lab
```

Open `01_train_and_serve.ipynb` and run it top to bottom, reading each explanation before
its cell:

1. Print the Python and library versions. They go into the session record.
2. Load the dataset and look at the rows, the ten inputs, and the target.
3. Split off a fifth of the rows for evaluation. Fit imputation, scaling, and Ridge
   regression as one pipeline on the training rows only.
4. Compare MAE and R² against a model that always predicts the training mean. Record both.
   Beating the mean is the whole ambition; the exercise is about closing the loop, not
   winning it.
5. Save the pipeline, its feature names, and the target name to `artifacts/model.joblib`.
   Save one input row to `example.json` and the notebook's prediction for it to
   `expected.json`.

Then restart the kernel and run all cells again. A notebook that only works because of a
cell that ran earlier and was later deleted is the first production risk of the exercise.
Two decisions in the save cell carry through the rest of the course: the request holds
inputs and never the target, and preprocessing is saved together with the estimator so
inference applies the same transformations as training.

### 4. Serve The Model Locally

In a second terminal, in `intro/` with `.venv` activated, record the installed versions
and start the service:

```bash
python -m pip freeze --exclude pywinpty --exclude pywin32 > requirements.lock.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

`requirements.lock.txt` lists the exact versions in this environment, including the
scikit-learn that fitted the model, and the Docker build installs exactly these. The two
`--exclude` flags drop packages JupyterLab installs only on Windows; they have no Linux
build, and a lock written on Windows without them fails inside the Linux image. On macOS
and Linux the flags change nothing. The lock also carries the notebook's dependencies into
the image, which is why the image ends up near a gigabyte; session 2 separates what the
service needs from what its author needed.

Read `api.py` while Uvicorn starts. It loads the artifact once, answers `GET /health`, and
accepts named numeric features at `POST /predict`. It checks that the names match the
saved schema, puts them in the saved order, and calls the pipeline. It never trains.

In a third terminal, also in `intro/`:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" --data-binary @example.json
```

In PowerShell, `curl` is an alias for something else; write `curl.exe`.

The first call returns `{"status":"ok","model_loaded":true}`. The second returns a
`prediction` and a `target`. The prediction has to equal the number in `expected.json`
down to floating-point noise. <http://127.0.0.1:8000/docs> shows the same two routes as a
generated page.

That is the test for today: a request to the service, then a real prediction. A network
`ping` would prove the machine is up and nothing about the model. These are manual
observations; automated tests arrive in session 3. The held-out evaluation in the notebook
is model evaluation, which is a different thing again.

Stop Uvicorn with Ctrl+C before the next step; the container wants the same port.

### 5. Pack The Service Into An Image

Read the `Dockerfile` first. It starts from a Python 3.12 image, installs the locked
dependencies, copies `api.py` and the saved model, and starts Uvicorn. The notebook and the
training data are not in the image: training happened before the build, and the image only
has to predict.

```bash
docker build -t intro-regression:session01 .
docker run --rm --name intro-regression -p 127.0.0.1:8000:8000 intro-regression:session01
```

The final dot is the build context, the directory whose files `COPY` may read. The first
build takes a few minutes. Leave the second command running. Inside the container Uvicorn
listens on `0.0.0.0:8000`; `-p` publishes that port at `127.0.0.1:8000` on the host.
`EXPOSE` in the Dockerfile documents the port and publishes nothing.

Repeat both `curl` commands from step 4. The request now goes into the container and the
answer comes from the model trained in the notebook. Compare the prediction with
`expected.json` once more.

### 6. Look Inside The Running Service

In another terminal:

```bash
docker ps
docker logs intro-regression
docker stop intro-regression
```

Find the container name and the port mapping in the first output and the two requests in
the second. After the stop, call `/health` again: the connection is refused. `--rm`
removed the stopped container; the image is still there and `docker run` starts a fresh
one.

When a step fails, the symptom points at the boundary that broke:

| Observation | First thing to inspect |
|---|---|
| Notebook import fails | which Python is active and whether `pip install` ran in it |
| API cannot find the model | the notebook's save cell and `artifacts/model.joblib` |
| Docker build cannot find the lock file | the `pip freeze` output and the current directory |
| Docker build fails compiling `pywinpty` | the lock was written without the `--exclude` flags; write it again |
| Host port is already allocated | a Uvicorn still running from step 4, or another container |
| Connection refused | `docker ps`, the logs, and the `-p` mapping |
| API returns 422 | feature names and numeric values in `example.json` |
| Prediction differs from the notebook | the artifact copied into the image and the installed versions |

Retraining changes the artifact and nothing else; the image holds the old model until it is
rebuilt and a new container started.

### 7. Explain What Was Built

Point at the notebook, the artifact, the lock file, the image, and the running container,
and say which changes on retraining, which must be rebuilt, and which is thrown away. Then
say why a reachable endpoint says nothing about whether the prediction is any good. The
service answers programs on this one machine; putting it in front of the checkout system,
controlling access, testing it, and watching it belong to sessions 8 through 11.

## Build A Second Regression

The homework repeats the path on a numeric target. Start with one change to the
walkthrough, another estimator or a subset of the features, then move to a different
dataset. A manageable sample is fine; keep enough rows for the held-out evaluation to mean
something and write down how the sample was chosen.

| Source | Target | Notes |
|---|---|---|
| [scikit-learn diabetes](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_diabetes.html) | disease progression after one year | 442 rows, ten features; already in hand through `load_diabetes(as_frame=True, scaled=False)` |
| [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) | daily rental count, `cnt`, in `day.csv` | `casual` and `registered` sum to the target, so leave them out; hold out the later dates rather than a random fifth |
| [UCI Concrete Compressive Strength](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) | compressive strength in MPa | numeric mixture quantities plus age; nothing to encode |

For public data, record the source URL, license, download date, target, feature units, and
how the sample was selected. For each feature, ask when it becomes known: a feature
observed after the prediction moment makes the offline score a lie. For demand over time,
hold out later dates instead of mixing past and future.

Categorical columns need encoding, and the encoding goes inside the saved pipeline, not in
the API. The supplied `api.py` accepts numeric features only; a model that needs strings
needs a new request schema. Regenerate `example.json` from the actual inputs.

What goes into the repository, under `intro/`: the notebook, the recorded metrics and
versions, `artifacts/model.joblib`, `requirements.lock.txt`, the Dockerfile,
`example.json`, one captured HTTP response, and a short note on what the target is and who
could act on the prediction. No test suite yet. `.venv/` is already in the repository's
`.gitignore` and stays out. Commit as the work progresses and tag the last commit
`session-01-done`, as the README describes. The bundled dataset does not count toward the
graded project's own-data requirement.

## Reading

- ASI module 1 deck (introduction) and module 2 deck (ML model lifecycle), with the CRISP-DM
  notes.
- ASI module 9, decks 1 and 6: IT system architecture and sourcing strategy. Skim them; they
  frame the build-or-buy choices the course makes in sessions 5, 6, and 12.
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/) and
  [Docker port publishing](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/):
  the image, startup command, and port mapping used today, explained by their authors.

## Homework

Run `baseline.py` on a second machine, or in a fresh virtual environment, or ask a classmate
to run it from a clean clone. Record whether it ran, which versions were installed, and
whether the three metrics match. Bring the record to session 2, where the differences are
the lab.

Finish the second regression. Bring the notebook's prediction and the container's response,
plus one sentence on the difference between installing libraries, training a model,
building an image, and running a service.

Start looking for a dataset. The graded project is built on the student's own problem and
data, not on HighRev; [PROJECT.md](../PROJECT.md) has the rules a dataset has to meet and
the proposal template. The proposal is due by the session 3 deadline, so two weeks of
looking start now. The sources above are a place to start; check any candidate against the
project rules.

## Checklist

- [ ] `baseline.py` runs locally and the metrics are recorded with the versions that produced them
- [ ] Each `COURSE NOTE` has a one-sentence failure written next to it
- [ ] The pair's trust list is grouped under the nouns of the course question
- [ ] `intro/` exists as a copy of `sessions/01_intro/` with a Python 3.12 environment and the libraries installed
- [ ] The notebook runs from a restarted kernel and saves the complete fitted pipeline
- [ ] MAE, R², and the installed versions are recorded
- [ ] The local API answers `/health` and returns the prediction in `expected.json`
- [ ] The image builds and the container returns the same prediction
- [ ] The student can say what the artifact, the image, the container, and the port mapping each are
- [ ] A source and numeric target are chosen for the second regression
- [ ] The homework record exists, even if the second run failed; a failure is a result
