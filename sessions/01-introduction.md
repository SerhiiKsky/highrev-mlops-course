# Session 01: The model lifecycle

A data scientist hands over `baseline.py`. It reads two CSV files, trains a model, reports a ROC AUC of 0.76, and saves a pickle. The business wants predictions at checkout next quarter. The model looks good. What happens next?

Today, you will map the model lifecycle and take a small model from a notebook to a Docker container that accepts HTTP requests. You will also identify what it takes to trust its predictions a year from now.

## The course problem

An online T-shirt shop wants to identify customers who will spend more than 300 in total. It plans to make this prediction at the first order and use it to allocate its retention budget. The binary target is `high_revenue`.

The data is in two files under `data/01_raw/`, committed to Git for now.

`customers.csv` has one row per customer:

| Column | Meaning |
|---|---|
| `customerID` | Customer identifier; joins to `orders.customer_id` |
| `gender` | M or F |
| `birthdate` | `YYYY/M/D`; three dates use February 29 in a non-leap year |
| `user_agent` | Browser string at sign-up; used to extract browser and OS |
| `ip_address` | Dropped before modeling |
| `campaign` | Whether the customer arrived through a campaign |
| `ip_address_country` | Country inferred from the IP address |

`orders.csv` has one row per order line:

| Column | Meaning |
|---|---|
| `order_date` | `YYYY/MM/DD` |
| `pages_visited` | Pages viewed during the order session |
| `order_id` | Order identifier |
| `customer_id` | Joins to `customers.customerID` |
| `tshirt_category` | Four categories with inconsistent spelling |
| `tshirt_price`, `tshirt_quantity` | Price × quantity gives the line total |

The baseline uses seven features: `pages_visited`, `age_first_order`, `gender`, `campaign`, `ip_address_country`, `browser`, and `os`.

## The lifecycle

CRISP-DM, covered in ASI module 2, has six stages: business understanding, data understanding, preparation, modeling, evaluation, and deployment.

`baseline.py` covers the middle four. This course extends the work through deployment, monitoring, and retraining. As new data arrives and conditions change, you need to evaluate and update the model without repeating every step by hand.

By session 12, you should be able to answer:

> Which code, environment, data, parameters, model, image, deployment, and monitoring records explain this prediction? What happens if the system stops working?

Today, you will build a service that another program on your machine can call. Later sessions make it reproducible, tested, tracked, and monitored.

## In class

1. Run `baseline.py`. Record the Python version, package versions, and three metrics.
2. Read the script. For each `COURSE NOTE`, write one sentence explaining the production risk.
3. In pairs, list what must be true to trust this model at checkout in twelve months. Group your answers by the items in the question above.
4. Compare your list with the README syllabus. Raise any gaps.
5. Complete the walkthrough. At each step, note what it produces and what the next step needs.

## From notebook to container

This exercise uses scikit-learn's diabetes dataset: 442 rows, ten numeric features, and a numeric target measuring disease progression after one year. It needs no download or data cleaning, so you can focus on deployment. This is a regression task, evaluated with MAE and R². It is not an assessment of medical usefulness.

HighRev remains the course's classification case study.

The supplied files are in [`01_intro/`](01_intro/):

| File | Purpose |
|---|---|
| `01_train_and_serve.ipynb` | Trains and evaluates the model; saves it with a sample request and expected prediction |
| `requirements.txt` | Lists the six required libraries |
| `api.py` | Loads the model and provides `/health` and `/predict` |
| `Dockerfile` | Packages the service, dependencies, and model |
| `.dockerignore` | Excludes the notebook, environment, and data from the image |

Work in a copy at the repository root:

```bash
cp -r sessions/01_intro intro
cd intro
```

Run the following commands from `intro/`. They use a POSIX shell; on Windows, use Git Bash unless noted otherwise.

### 1. Check Docker

Install and start Docker Desktop on Windows or macOS, or Docker Engine on Linux. Then run:

```bash
docker --version
docker run --rm hello-world
```

The first command prints the client version. The second downloads an image and runs a container.

An **image** packages files and a startup command. A **container** is an instance of that image. If Docker cannot reach the daemon, check that the engine is running.

### 2. Set up Python

Read `requirements.txt`, then create a Python 3.12 environment and install the libraries:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, replace the first two commands with:

```bash
py -3.12 -m venv .venv
source .venv/Scripts/activate
```

pandas handles tables, scikit-learn provides the dataset and model, and joblib saves the fitted pipeline. FastAPI and Uvicorn serve HTTP requests. JupyterLab runs the notebook.

Installing these libraries prepares the environment. Training creates the model.

### 3. Train and save the model

```bash
python -m jupyter lab
```

Open `01_train_and_serve.ipynb`. Read the explanations and run the cells in order:

1. Record the Python and library versions.
2. Inspect the dataset, inputs, and target.
3. Hold out 20% of the rows for evaluation. Fit imputation, scaling, and Ridge regression as one pipeline using only the training rows.
4. Compare MAE and R² with a model that always predicts the training mean. Record both models' scores.
5. Save the fitted pipeline, feature names, and target name to `artifacts/model.joblib`. Save one input row to `example.json` and its prediction to `expected.json`.

Restart the kernel and run all cells again to check that the notebook works from a clean state.

Keep preprocessing and the estimator in the same saved pipeline so training and prediction use the same transformations. Requests contain input features only, never the target.

### 4. Run the local service

Open a second terminal in `intro/` and activate `.venv`. Record the installed versions and start the API:

```bash
python -m pip freeze --exclude pywinpty --exclude pywin32 > requirements.lock.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Docker will install the versions in `requirements.lock.txt`, including the scikit-learn version used for training. The exclusions remove two Windows-only packages that would fail in the Linux image. They have no effect on macOS or Linux.

This file also includes notebook dependencies, making the image large. Session 2 separates training and service dependencies.

Read `api.py`. It loads the model once, checks feature names, puts them in the saved order, and returns predictions. It does not train the model.

In a third terminal, also in `intro/`, run:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" --data-binary @example.json
```

If using PowerShell, write `curl.exe` instead of `curl`.

The health response should be `{"status":"ok","model_loaded":true}`. The prediction response contains `prediction` and `target`. Compare the prediction with `expected.json`; they should match apart from tiny floating-point differences. You can also inspect the API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

These manual checks show that the service responds and reproduces the notebook's prediction. The held-out scores measure model quality. Automated tests come in session 3.

Stop Uvicorn with Ctrl+C to free port 8000.

### 5. Build and run the image

Read the `Dockerfile`. It starts from Python 3.12, installs the locked dependencies, copies the API and saved model, and starts Uvicorn. Training happens before the build, so the notebook and training data are excluded.

```bash
docker build -t intro-regression:session01 .
docker run --rm --name intro-regression -p 127.0.0.1:8000:8000 intro-regression:session01
```

The final dot sets the current directory as the build context: the files Docker can copy. The first build may take a few minutes. Leave the container running.

Uvicorn listens on `0.0.0.0:8000` inside the container. The `-p` option makes it available at `127.0.0.1:8000` on your machine. `EXPOSE` in the Dockerfile documents the port; it does not publish it.

Repeat both `curl` commands from step 4. Compare the container's prediction with `expected.json`.

### 6. Inspect and stop the container

In another terminal, run:

```bash
docker ps
docker logs intro-regression
docker stop intro-regression
```

Find the container name and port mapping in `docker ps`, then find your requests in the logs.

Call `/health` after stopping the container. The connection should fail. The `--rm` option removes the stopped container, but the image remains. Use `docker run` to start a new container.

| Problem | Check first |
|---|---|
| Notebook import fails | Active Python environment and installed packages |
| API cannot find the model | Notebook save cell and `artifacts/model.joblib` |
| Docker cannot find the lock file | `pip freeze` output and current directory |
| Docker build fails on `pywinpty` | Regenerate the lock file with both `--exclude` flags |
| Port is already allocated | Local Uvicorn process or another container |
| Connection refused | `docker ps`, logs, and port mapping |
| API returns 422 | Feature names and numeric values in `example.json` |
| Prediction differs from the notebook | Model copied into the image and installed versions |

After retraining, rebuild the image and start a new container to serve the updated model.

### 7. Explain what you built

Identify the notebook, saved model, lock file, image, and container. Explain what changes after retraining, what must be rebuilt, and what can be discarded.

Explain why a working endpoint does not prove that its predictions are useful. This service is available only on your machine. Checkout integration, access control, deployment testing, and monitoring follow in sessions 8–11.

## Homework

### Check reproducibility

Run `baseline.py` on another machine, in a fresh environment, or from a classmate's clean clone. Record whether it runs, the installed versions, and whether the three metrics match. Bring the record to session 2, including any failures.

### Build a second regression

First, change one part of the walkthrough: try another estimator or a subset of features. Then repeat the process with a different dataset and a numeric target.

| Dataset | Target | Notes |
|---|---|---|
| [scikit-learn diabetes](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_diabetes.html) | Disease progression after one year | Use for the first variation; load with `load_diabetes(as_frame=True, scaled=False)` |
| [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) | Daily rentals: `cnt` in `day.csv` | Exclude `casual` and `registered`, which sum to the target. Hold out later dates. |
| [UCI Concrete Compressive Strength](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) | Compressive strength in MPa | Numeric mixture quantities and age; no categorical encoding needed |

You may use a sample. Keep enough rows for a useful evaluation and explain how you selected them. Record the source URL, license, download date, target, and feature units.

Use only features available when the prediction would be made. For time-based demand, evaluate on later dates rather than mixing past and future.

Put any categorical encoding inside the saved pipeline. The supplied API accepts numeric features only, so string inputs require a new request schema. Regenerate `example.json` from the actual inputs.

Commit the following under `intro/`:

- Notebook, metrics, and recorded versions
- `artifacts/model.joblib` and `requirements.lock.txt`
- `Dockerfile`
- `example.json` and one captured HTTP response
- A short note describing the target, who could use the prediction, and the data source and sampling details

No test suite is required yet. Keep `.venv/` out of Git; it is already in `.gitignore`. Commit as you work and tag the final commit `session-01-done`, following the README.

Bring the notebook's prediction and the container's response. In one sentence, distinguish installing libraries, training a model, building an image, and running a service.

### Choose a project dataset

The graded project uses your own problem and data. HighRev and the bundled dataset do not meet that requirement.

Read [PROJECT.md](../PROJECT.md) for dataset rules and the proposal template. Start looking now: the proposal is due by the session 3 deadline, in two weeks. Check any candidate against the project rules.

## Reading

- ASI modules 1 and 2, including the CRISP-DM notes
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Docker port publishing](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/)

## Checklist

- [ ] Record baseline metrics and versions; explain each `COURSE NOTE` risk.
- [ ] Group your pair's trust requirements and compare them with the syllabus.
- [ ] Create `intro/` and install the libraries in a Python 3.12 environment.
- [ ] Run the notebook from a restarted kernel; save the full pipeline and record MAE and R².
- [ ] Confirm that the local API and container return the expected prediction.
- [ ] Explain the saved model, image, container, and port mapping.
- [ ] Record the clean-environment baseline run, including any failures.
- [ ] Complete the second regression and commit the required files.
- [ ] Begin choosing a dataset for the project proposal.
