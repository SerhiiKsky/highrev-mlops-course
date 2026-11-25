# Session 09 notes — operating the containerized system

Copy this file to `notes/session-09.md` in your exercise project. Record what you
observed, with the command that showed it. These notes are not graded; E6 uses them
as evidence.

## Starting point

- Lab 08 exit commit (`git log --oneline -2`: the line below the starter commit):
- Starter commit:
- Lab 06 run directory (`$run`):
- Docker and Compose versions (`docker version --format '{{.Server.Version}}'`, `docker compose version`):

## L09-E1 Inventory

Fill from `docker compose config`, `docker compose images`, the Dockerfiles and
`docker inspect`. Do not start fixing anything yet.

| Service | Image | Built from (Dockerfile, environment) | User inside | Command / entrypoint | Host port → container port | Mounts (host or volume → container path) | Health check (what it requests) |
|---|---|---|---|---|---|---|---|
| mlflow | | | | | | | |
| api | | | | | | | |
| project (job) | | | | | | | |
| ag (job) | | | | | | | |

- Where the API expects its model and pointer (inside the container):
- Where you will put them on your machine:
- Where MLflow keeps runs and artifacts:
- Where a monitoring report written by a job ends up on your machine:
- Anything in the inventory that looks inconsistent to you (write it down, do not fix it yet):

## L09-E2 Running, live, ready

| Check | Command | Before repair | After repair, no model deployed |
|---|---|---|---|
| Container state | `docker compose ps` | | |
| Last health-check result | `docker inspect --format '{{json .State.Health}}' highrev-api-1` | | |
| Liveness | `curl -s http://127.0.0.1:8007/health` | | |
| Readiness | `curl -s -w ' %{http_code}\n' http://127.0.0.1:8007/ready` | | |
| One prediction | `curl … /predict` (brief) | | |

- What a green `docker compose ps` proved, and what it did not:
- Which endpoint a health check for an ML service must call, and why:

## L09-E3 Mounts and recreation

Mount check after deploying v1:

| Check | Command | Before repair | After repair |
|---|---|---|---|
| What the daemon mounted | `docker inspect -f '{{json .Mounts}}' highrev-api-1` | | |
| What the API sees | `docker compose exec api ls -A /serving` | | |
| What you deployed | `ls serving` | | |
| Reload | `curl -X POST … /admin/reload` | | |

Recreation table. Before each command note the container id
(`docker inspect -f '{{.Id}}' highrev-api-1 | cut -c1-12`) and `loaded_at` from `/health`.

| Command | `mlflow` kept or recreated | `api` kept or recreated | Why |
|---|---|---|---|
| `docker compose up -d api` (nothing changed) | | | |
| `docker compose up -d api` after editing the api health check | | | |
| `docker compose up -d api` after editing the api mounts | | | |
| `ADMIN_TOKEN=rotated docker compose up -d api`, then `docker compose up -d api` again | | | |
| a job with `docker compose run --rm -T --no-deps project …` vs without `--no-deps` (brief) | | | |

- What Compose compares before it decides to recreate a container:
- Why a recreated API still served the same model:

## L09-E4 The monitoring cycle in containers

- Exit code and last lines of the first `bash scripts/cycle.sh none`:
- What the tracking job wrote to stdout (`printf '%q\n' "$(cat /tmp/track.out)"`):
- What it wrote to stderr:
- Your repair (one line):
- Last lines of the repaired run:

| Identity | Value | Where you read it |
|---|---|---|
| Model the API serves | | `/health` |
| Model the pointer names | | `serving/current.json` |
| Model the batches were scored with | | `scores.csv` column `model_version` |
| Commit and data hash in `scores.csv` | | |
| MLflow run id | | MLflow UI, experiment `lab09-monitoring` |

- `scores.csv` first row compared with your Lab 08 `scores.csv` for the same day:
- Where the MLflow run and its `scores.csv` artifact live now that the job container is gone:
- Where `drift.html` would be if the job had written it outside a mounted folder:
- What `MLFLOW_TRACKING_URI=http://localhost:5000` does inside a job container, and why:

## L09-E5 Deploy, verify, roll back

| Step | Command | `/health` `model_version` | Reload answer (`before` → `after`, or the error) | Container id |
|---|---|---|---|---|
| v1 serving | | | | |
| deploy v2 | | | | |
| roll back to v1 | | | | |
| bad deploy | | | | |
| pointer restored | | | | |
| after `docker compose down` and `up -d mlflow api` | | | | |

- Rollback duration you measured, and what it consisted of:
- Why the `/predict` values of v1 and v2 cannot tell you which model serves:
- What would happen at the next container restart if you had left the bad pointer in place:
- What survived `down`/`up`, and what `down -v` would have destroyed:

## Incident table

One row per incident you met in E2–E4. Bug class: application, container
configuration, host operating-system difference, or integration/interface.

| Incident (as you first saw it) | Observe (symptom) | Investigate (diagnostic command and what it showed) | Explain (cause; bug class) | Repair (minimal change) | Verify (acceptance test) | Prevent (how to avoid it in production) |
|---|---|---|---|---|---|---|
| E2: the API looks healthy but cannot predict | | | | | | |
| E3: a deployed model is not seen | | | | | | |
| E4: the cycle stops after the tracking step | | | | | | |

## L09-E6 Acceptance decision

- Approve or reject the system for the next lab, with the evidence rows above that support it:
- One risk that remains:
