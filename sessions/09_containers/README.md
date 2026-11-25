# Lab 09 student assets

Start with the [student brief](../09-operating-containers.md). Work in your own
individual exercise project at its Lab 08 exit commit, never in the course checkout
or the team project. The brief's "Before class" section has the exact copy commands.
They refuse to overwrite existing files; compare and merge instead.

You receive a complete containerized system. You write no Python in this lab: you
inspect the system, find out why it misbehaves, repair its configuration, and
operate it (deploy, verify, roll back). Treat every supplied file as something a
colleague handed over: it may contain mistakes.

| Course asset | Destination in your exercise project | Purpose | Your work |
| --- | --- | --- | --- |
| [starter/compose.yaml](starter/compose.yaml) | `compose.yaml` | Services `mlflow` and `api`, job runners `project` and `ag`, ports, mounts, health checks | inspect (E1), repair (E2–E3) |
| [starter/docker/project.Dockerfile](starter/docker/project.Dockerfile) | `docker/project.Dockerfile` | Project environment image (Python 3.12, root `uv.lock`): MLflow server and project jobs | inspect (E1) |
| [starter/docker/autogluon.Dockerfile](starter/docker/autogluon.Dockerfile) | `docker/autogluon.Dockerfile` | AutoGluon environment image (Python 3.11, `lab07/uv.lock`): live API and AutoGluon jobs | inspect (E1) |
| [starter/.dockerignore](starter/.dockerignore) | `.dockerignore` | What the build may see: lock files and the serving code only | read (homework) |
| [starter/lab07/lab07/live_api.py](starter/lab07/lab07/live_api.py) | `lab07/lab07/live_api.py` | Prediction API with live/ready split, model loaded from a pointer, reload | read |
| [starter/scripts/cycle.sh](starter/scripts/cycle.sh) | `scripts/cycle.sh` | One Lab 08 monitoring window, every stage in a container, ending with an identity check | run, repair (E4) |
| [starter/src/highrev/monitoring/track.py](starter/src/highrev/monitoring/track.py) | `src/highrev/monitoring/track.py` | Records a monitoring window in MLflow; reports the served and the scored model | read |
| [incident-table.md](incident-table.md) | `notes/session-09.md` | Inventory, evidence per exercise, incident table | fill in |
| [checklist.md](checklist.md) | read, or append to your notes | Ungraded self-check | tick |
| [challenges.md](challenges.md) | — | Optional troubleshooting challenges after E6 | optional |

Your own Lab 07 and Lab 08 code (`lab07/lab07/api.py`, `score_batches.py`,
`train.py`, `src/highrev/monitoring/`) is used unchanged. The setup adds `serving/`
to `.gitignore`: models, pointer and prediction logs are deployment state, not code.

## Where state lives

| State | Location on your machine | Inside the containers | Survives `docker compose down` |
| --- | --- | --- | --- |
| Served model folders and pointer | `serving/models/<version>/`, `serving/current.json` | `/serving` (api read-write, `ag` read-only, `project` read-write) | yes (a host folder) |
| Prediction log | `serving/predictions/<date>.jsonl` | `/serving/predictions/` | yes |
| MLflow runs and artifacts | Docker volume `highrev_mlflow` | `/mlflow` in `mlflow` | yes; `down -v` deletes it |
| Streams and monitoring reports | `data/05_serving/lab09/`, `data/08_reporting/monitoring/lab09/` | `/workspace/data/...` | yes |
| Anything a container writes elsewhere | nowhere | the container's own filesystem | no |

## Service contract

Base URL from your machine: `http://127.0.0.1:8007`. Inside the Compose network:
`http://api:10000`. MLflow: `http://127.0.0.1:5000` from your machine,
`http://mlflow:5000` from a job container.

| Endpoint | Answers |
| --- | --- |
| `GET /health` | always 200 while the process runs: `status`, `ready`, `model_version`, `registry_version` (`null` until Lab 10), `data_hash`, `loaded_at`, `source_revision`, `error` (the last load or reload failure) |
| `GET /ready` | 200 with the model identity when a model is loaded; 503 with `error` otherwise |
| `POST /admin/reload` | header `X-Admin-Token: local-admin-token`; loads the model the pointer names. 200 `{"before", "after", …}`; 409 when the new model cannot be loaded (the old one keeps serving, `still_serving`); 403 with a wrong token |
| `POST /predict` | the Lab 07 request and response; response header `X-Model-Version`; appends one line to the prediction log |

The pointer `serving/current.json`:

```json
{"model_version": "lab07-v1", "path": "models/lab07-v1", "registry_version": null, "data_hash": "<md5 line of data/01_raw.dvc>"}
```

`path` is relative to `serving/`. The folder's `lab07-model.json` must name the same
`model_version`, or the API refuses to load it.

## Files the commands write

| Command (project root, Git Bash) | Writes |
| --- | --- |
| `docker compose build` | images `highrev-project:local`, `highrev-autogluon:local` |
| `docker compose up -d mlflow api` | containers `highrev-mlflow-1`, `highrev-api-1`; volume `highrev_mlflow` on first start |
| `bash scripts/cycle.sh <incident>` (with `run` exported, as in Before class) | `data/05_serving/lab09/<incident>/` (once), `data/08_reporting/monitoring/lab09/<incident>/` (each run), one MLflow run in experiment `lab09-monitoring` |
| `docker compose run --rm -T --no-deps -v "$run:/run:ro" ag python -m lab07.train …` | the model folder you name with `--output` |
| `curl -X POST … /admin/reload` | nothing on disk; the API's loaded model and `/health` change |

On Windows, run Docker commands from Git Bash with `export MSYS_NO_PATHCONV=1` so that
paths such as `/serving/...` reach Docker unchanged.
