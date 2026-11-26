# Lab 09 — Operating a containerized ML serving system

## Incident and goal

"`docker compose up` printed *Started*, `docker ps` said *healthy*, and every
prediction failed. We deployed a new model and the API kept answering with the old
one. The monitoring job ran green, yet nobody could say which model it had scored."

A colleague has packaged the HighRev system in containers: an MLflow tracking
server, the live prediction API, and job containers that run your Lab 08 monitoring
cycle. You receive it complete, and it misbehaves. In this individual, ungraded lab
you act as the engineer on call. You write no Python. You inspect the system, find
out why it misbehaves, repair its configuration, and operate it: deploy a model,
verify which model serves, roll back, and show what survives a restart.

The question behind every exercise: **are we monitoring the model we actually
serve, or the model we think we serve?**

By the end you can:

1. inventory a Compose system: images, users, ports, mounts, health checks, and where
   each piece of state lives;
2. tell a running container, a live API and a ready API apart, and write a health
   check that tests what matters for an ML service;
3. diagnose a mount that silently points at the wrong folder, and predict which
   change makes Compose recreate which container;
4. run the Lab 08 monitoring cycle in containers and prove that the scored model is
   the served model;
5. deploy, verify by identity, and roll back a model without rebuilding an image.

Every incident is worked the same way: **Observe** (the symptom) → **Investigate**
(a command that shows the cause) → **Explain** (the cause and its bug class:
application, container configuration, host operating-system difference, or
integration/interface) → **Repair** (the smallest change) → **Verify** (an
acceptance test) → **Prevent** (what stops it in production). Keep your notes in
`notes/session-09.md`, started from the [notes template](09_containers/incident-table.md).
The [final project rubric](../FINAL_PROJECT_RUBRIC.md) governs project grading; the
[checklist](09_containers/checklist.md) at the end is not graded.

## Before class

You need your own exercise project at its **Lab 08 exit**: the Lab 08 code and tests
committed, `lab07/model/` with its `lab07-model.json`, and the Lab 08 scores of the
clean stream in `data/08_reporting/monitoring/none/scores.csv`. You also need the Lab
06 run directory your Lab 07 model was trained from, and **Docker Desktop** (Windows,
macOS) or Docker Engine with the Compose plugin (Linux), running.

Commands are Bash (Git Bash on Windows, as in Labs 07 and 08). Run this block in
**every new terminal**; replace the three paths with your own absolute paths:

```bash
course='/path/to/highrev-mlops-course'
project='/path/to/your-exercise-project'
run='/path/to/your-lab06-run'
export MSYS_NO_PATHCONV=1 run            # Git Bash: pass /serving, /run ... to Docker unchanged
cd "$project"
api=http://127.0.0.1:8007
token=local-admin-token
row='{"pages_visited":3,"age_first_order":30,"gender":"F","campaign":true,"ip_address_country":"PL","browser":"Chrome","os":"Windows"}'
data_hash=$(sed -n 's/.*md5: //p' data/01_raw.dvc)
v1=$(sed -n 's/.*"model_version": *"\([^"]*\)".*/\1/p' lab07/model/lab07-model.json)
# Write the serving pointer atomically: a temporary file, then a rename.
point() { printf '{"model_version": "%s", "path": "models/%s", "registry_version": null, "data_hash": "%s"}\n' \
  "$1" "$1" "$data_hash" > serving/.current.json.tmp && mv serving/.current.json.tmp serving/current.json \
  && cat serving/current.json; }
reload() { curl -s -w ' [HTTP %{http_code}]\n' -X POST -H "X-Admin-Token: $token" "$api/admin/reload"; }
# After `up` (re)creates the API: wait until it answers HTTP at all, ready or not.
wait_api() {
  local attempt
  for attempt in {1..30}; do
    if curl -s --connect-timeout 1 --max-time 2 "$api/ready" > /dev/null; then return 0; fi
    sleep 1
  done
  echo "STOP: API did not answer; inspect docker compose ps -a and docker compose logs api" >&2
  return 1
}
echo "model $v1, data $data_hash"
```

`MSYS_NO_PATHCONV=1` matters on Windows: without it, Git Bash rewrites every argument
that looks like a Unix path, so `docker compose exec api ls /serving` asks the
container for `C:/Program Files/Git/serving`. The price: a Windows program no longer
understands `/dev/null` as an argument (`curl -o /dev/null` fails with exit 23), so
this brief redirects with `> /dev/null`, which the shell handles. `point`, `reload` and
`wait_api` are helpers for E3 and E5; `point` creates nothing until `serving/` exists. `export run` makes the
Lab 06 path visible to `scripts/cycle.sh`. `wait_api` accepts any HTTP response,
including 503: it checks reachability, not readiness. If it prints `STOP`, do not
continue dependent commands; inspect the named state/logs, repair the startup
failure and rerun the wait. Final acceptance also requires Docker's health verdict.

Readiness check:

```bash
test -f lab07/model/lab07-model.json && echo "model ok"
test -f "$run/comparison/training-input/fit.csv" && echo "run ok"
test -f data/08_reporting/monitoring/none/scores.csv && echo "lab 08 scores ok"
git status --short
docker version --format 'docker {{.Server.Version}}'
docker compose version
docker info --format 'memory for containers: {{.MemTotal}} bytes'
```

All three checks must print `ok`, and `git status --short` should print nothing:
commit or put aside unfinished work first. If only the Lab 08 scores are missing (the
folder is ignored by Git, so a fresh clone or a cleaned checkout lacks it), recreate
them with Lab 08's clean-stream steps: `simulate --incident none` from
[L08-E1](08-drift-and-monitoring.md#l08-e1--the-serving-stream-and-the-taxonomy) step 2
and the `score_batches` command from
[L08-E3](08-drift-and-monitoring.md#l08-e3--score-with-delayed-labels). The simulator's
fixed seed gives the same rows again. The memory line should show at least
4 000 000 000 bytes. Docker Desktop on Windows gives its Linux VM half of your RAM by
default; the system uses about 2 GB at rest, most of it MLflow, and a few hundred MB
more while a job runs.

Update your course checkout and read the [asset list](09_containers/README.md). Then
install the starter. The first block refuses to copy if any destination exists:

```bash
cd "$project"
starter="$course/sessions/09_containers/starter"
clash=0
for f in compose.yaml .dockerignore docker scripts/cycle.sh lab07/lab07/live_api.py \
         src/highrev/monitoring/track.py serving; do
  [ ! -e "$f" ] || { echo "STOP: $f exists; inspect it before copying"; clash=1; }
done
[ "$clash" = 0 ] && cp -R "$starter/compose.yaml" "$starter/.dockerignore" "$starter/docker" . \
  && mkdir -p scripts && cp "$starter/scripts/cycle.sh" scripts/ \
  && cp "$starter/lab07/lab07/live_api.py" lab07/lab07/ \
  && cp "$starter/src/highrev/monitoring/track.py" src/highrev/monitoring/ \
  && echo "starter copied"
grep -qx 'serving/' .gitignore || printf '\n# Lab 09\nserving/\n' >> .gitignore
```

If a `STOP` line prints, nothing was copied: compare the existing file with the
starter, keep your work, and copy the remaining files one by one. `serving/` is
deployment state (models, pointer, prediction log), not code, so Git ignores it.
Commit the setup, then build both images with that commit as their source revision:

```bash
git add compose.yaml .dockerignore docker scripts/cycle.sh lab07/lab07/live_api.py \
  src/highrev/monitoring/track.py .gitignore
git commit -m "Lab 09: containerized system starter"
SOURCE_REVISION=$(git rev-parse --short HEAD) docker compose build
docker image ls 'highrev-*'
docker compose config --quiet && echo "compose ok"
```

The build downloads the base images and every locked package: about 5 GB on disk
(`highrev-project:local` 3.4 GB, `highrev-autogluon:local` 1.7 GB). On the
instructor's machine with a fast connection it took 45 s and 90 s; it can take much
longer at home, which is why it happens before class. `compose ok` means the file is
valid YAML with valid keys, nothing more: the system has faults that `config` cannot
see. Do not start the system yet. No push is needed in this lab.

## Concepts

**Image, container, layer.** An image is a read-only stack of layers, one per
Dockerfile instruction; a container is a running process started from an image, with
a thin writable layer on top. Docker rebuilds a layer only when its instruction or its
inputs change, and then every layer after it. The two Dockerfiles copy the lock files
before the code: a code change rebuilds in seconds, a lock change reinstalls the
whole environment (measured on the instructor's machine: 2.4 s versus 37 s for the
AutoGluon image).

**Containers are disposable.** Removing a container (`docker compose down`, or
replacement during recreation) discards its writable layer. A process crash or a
stop/start of the same container keeps that layer. Anything that must survive
container removal lives outside: in a **bind mount**
(a host folder mapped into the container, here `./serving` and the project itself) or
a **named volume** (storage Docker manages, here `highrev_mlflow` for runs and
artifacts), or in another service (the MLflow server). A file a job writes anywhere
else is gone when its `--rm` container is removed.

**Two environments, two images.** The project environment (Python 3.12, root
`uv.lock`) runs the MLflow server and the project jobs (`simulate`, `validate`,
`track`). The AutoGluon environment (Python 3.11, `lab07/uv.lock`) runs the live API
and the AutoGluon jobs (scoring, training). They exchange only files, as in Lab 08.
Jobs run with your project mounted at `/workspace`, so they use the code, parameters
and data on your disk; the images supply only the locked environments.

**Running, live, ready.** *Running*: the container's process exists. *Live*: the
process answers HTTP (`GET /health`, always 200, with the model identity and the last
error). *Ready*: a model is loaded and `/predict` can answer (`GET /ready`, 200 or
503). An ML API that starts without a model is running and live but not ready. A
**health check** is a command Docker runs inside the container at an interval;
after a number of consecutive failures the container is marked `(unhealthy)`.
Docker does not restart an unhealthy container by itself; it reports it, and load
balancers and orchestrators act on it. A health check is only as good as the
question it asks.

**The serving pointer.** The API loads the model named by `serving/current.json`:
`model_version`, the folder `path` (relative to `serving/`), `registry_version`
(`null` until Lab 10) and the data hash. The folder's `lab07-model.json` must name
the same version, or the API refuses it. Deploying is: copy a model folder, rewrite
the pointer, call `POST /admin/reload`. A reload that fails leaves the previous model
serving (409 `still_serving`). No image is rebuilt.

**Compose is desired state.** `docker compose up` compares the *resolved*
configuration of each service (after variables from your shell are filled in) with a
hash stored on its running container. If they differ, Compose stops, removes and
recreates the container; if not, it leaves it running. `docker compose run` starts a
one-off job container and, unless you pass `--no-deps`, first brings its
dependencies to the desired state, which can recreate a service you never meant to
touch.

**Names, not `localhost`.** Inside a container, `localhost` is that container. Services
on the Compose network reach each other by service name: a job reaches MLflow at
`http://mlflow:5000` and the API at `http://api:10000`. Your machine reaches them
through published ports, bound to loopback only: `http://127.0.0.1:5000` and
`http://127.0.0.1:8007`.

**Served versus scored.** The batch scorer loads a model from a path; the API loads
the model the pointer names. Nothing forces these to be the same. `scripts/cycle.sh`
scores with the pointer's model and then checks that the model the API reports equals
the model in `scores.csv`.

## Resuming after a break

In a new terminal, run the Before class variable block again, then look before
changing anything:

```bash
git log --oneline -5                      # your last Lab 09 commit names the exercise
git status --short                        # repairs not yet committed
docker compose ps                         # what is running, and its health
cat serving/current.json 2>/dev/null      # the pointer, if E3 has deployed
curl -s "$api/health"; echo
ls data/05_serving/lab09 2>/dev/null      # streams the cycle already simulated
```

Repeat inspection commands freely; check the copy and training guards in E3 and E5
before repeating mutations. Before `docker compose up -d mlflow api`, inspect your
pending configuration edits and pointer: recreation loads the pointer on disk, so
restore a refused deploy's pointer first (E5).
Never run `docker compose down -v` (it deletes your MLflow runs). Continue from the
first step of your exercise whose evidence is missing in your notes.

## L09-E1 — Inventory the supplied system

**Purpose:** know what you operate before you change it. Every later diagnosis compares
what you see with this inventory.
**Start:** setup committed, images built, nothing started. Project root, one terminal.

1. Copy the [notes template](09_containers/incident-table.md) to `notes/session-09.md`
   and fill its Starting point section.
2. Read `compose.yaml`, `docker/project.Dockerfile` and `docker/autogluon.Dockerfile`.
   Then let Docker tell you what it will actually do:

   ```bash
   docker compose --profile jobs config            # resolved: every variable filled in
   docker compose --profile jobs config --services
   for i in highrev-project:local highrev-autogluon:local; do
     docker image inspect "$i" --format "$i user={{.Config.User}} cmd={{json .Config.Cmd}} workdir={{.Config.WorkingDir}}"
   done
   docker image history highrev-autogluon:local
   ```

3. Fill the inventory table: one row per service and job. A `user:` line in
   `compose.yaml` overrides the image's user; an empty image user means root. Fill the
   four "where" lines below the table. Write down anything that looks inconsistent,
   but do not fix it yet.

**Expected result:** four rows: `mlflow` and `api` run continuously, `project` and
`ag` are jobs (profile `jobs`) that only start with `docker compose run`. `mlflow`
and `api` publish loopback ports; the jobs publish none. The API expects its pointer
at `/serving/current.json` inside its container. MLflow keeps runs in the volume
mounted at `/mlflow`; reports written by jobs land in your project folder, because the
project is mounted at `/workspace`. The `uv sync` layer is about 1 GB of the AutoGluon
image; the code layer is tens of kilobytes.

**Check:** which services can lose data when their container is removed, and which
cannot? Why does `ag` run as root while `api` does not? What would `docker compose up`
start, and what would it not?

**Failure and recovery:** `config` fails with a variable or YAML error: the copy is
incomplete or edited; compare with the starter. `No such image`: the build did not
finish; rerun the build command from Before class and read its first error.
**Checkpoint E1:** inventory filled; nothing running. **Handoff:** commit your notes.

## L09-E2 — The API is healthy, and cannot predict

**Purpose:** find out what "healthy" means for an ML service, and make the health check
test it.
**Start:** E1. Nothing deployed: `serving/` does not exist yet.

1. Start the platform and watch it:

   ```bash
   docker compose up -d mlflow api
   docker compose ps
   ```

   Repeat `docker compose ps` until both services show `(healthy)`.
2. **Observe.** Ask the API for a prediction:

   ```bash
   curl -s -w ' [HTTP %{http_code}]\n' -H 'Content-Type: application/json' -d "$row" "$api/predict"
   ```

3. **Investigate.** Fill the E2 ladder in your notes, column "Before repair":

   ```bash
   docker inspect --format '{{json .State.Health}}' highrev-api-1
   curl -s "$api/health"; echo
   curl -s -w ' [HTTP %{http_code}]\n' "$api/ready"
   docker compose logs --tail 20 api
   ```

   Which request does the health check send, and what does that endpoint prove?
4. **Repair.** Decide which endpoint the API's health check must call so that a
   container without a model is *not* reported healthy. Change only that in the `api`
   service of `compose.yaml`, then apply it and watch over about a minute:

   ```bash
   docker compose up -d api
   docker compose ps
   ```

5. **Verify.** Fill the column "After repair, no model deployed". Write the incident
   row "E2" of your incident table (all six columns and the bug class).

**Expected result:** before the repair, `api` turns `(healthy)` within a few seconds while
`/predict` answers 503 `{"detail":"No model loaded"}`; `/health` answers 200 with
`"ready":false` and `error` `FileNotFoundError: No /serving/current.json: nothing
deployed yet`; `/ready` answers 503; the log shows startup complete and no error. After
the repair, `up` prints `Recreate`, `api` shows `(health: starting)` and turns
`(unhealthy)` after about 50 s (a 30 s start period, then three failed checks 10 s
apart). That is the correct verdict: there is no model.

**Check:** what did the green status prove, and what did it not? Why is the unhealthy
API after your repair an improvement? Who, other than you, acts on the health state?

**Failure and recovery:** `curl: (7) Failed to connect` on 8007: the API is not running
(`docker compose ps -a`, then `docker compose logs api`) or another program, often the
Lab 07 container, holds port 8007 (`docker ps`; stop the old container). Both
services `unhealthy` or restarting: see the troubleshooting table (memory). Your edit
makes `config` fail: restore with `git checkout -- compose.yaml` and edit again.
**Checkpoint E2:** health check repaired, `api` unhealthy without a model, the E2 row
written. **Handoff:** commit `compose.yaml` and your notes ("Lab 09 E2: …").

## L09-E3 — A deployed model the API cannot see

**Purpose:** deploy the first model, find out why the API ignores it, and learn which
changes recreate a container.
**Start:** E2 committed; `mlflow` healthy, `api` unhealthy without a model.

1. Deploy your Lab 07 model as the first serving version. **First copy only:** check
   `ls "serving/models/$v1"` before the block. If that directory already exists,
   skip `cp -R`: repeating it nests a second `model/` directory. Check that
   `diff -qr lab07/model "serving/models/$v1"` prints nothing, then resume with
   `point "$v1"` and `reload`. If it differs or is incomplete, stop, preserve the
   directory and diagnose the interrupted copy before changing the pointer.

   ```bash
   mkdir -p serving/models
   cp -R lab07/model "serving/models/$v1"
   point "$v1"
   reload
   ```

2. **Observe.** Read the reload answer, `curl -s "$api/health"`, and `ls`. Is there a
   folder in your project that you did not create?
3. **Investigate.** Fill the mount check in your notes, column "Before repair":

   ```bash
   docker inspect -f '{{json .Mounts}}' highrev-api-1
   docker compose exec api ls -A /serving
   ls -A serving
   ```

   The Docker daemon, not your shell, resolves the host side of a bind mount. What does
   it do when that folder does not exist?
4. **Repair** the `api` mount in `compose.yaml`, apply it, and remove what the fault
   left behind. The API loads the model when it starts, so no reload is needed:

   ```bash
   docker compose up -d api && wait_api
   rmdir FOLDER; ls -A          # FOLDER: the empty folder the fault created (step 2)
   docker compose ps
   curl -s "$api/health"; echo
   ```

   With a model loaded, one more request for the record: `$row` with `"browser":null`
   instead of `"browser":"Chrome"`. Note the status and the probability:

   ```bash
   curl -s -w ' [HTTP %{http_code}]\n' -H 'Content-Type: application/json' \
     -d "${row/\"browser\":\"Chrome\"/\"browser\":null}" "$api/predict"
   ```

   Fill "After repair", write incident row "E3", and commit the repair:
   `git commit -am "Lab 09 E3: API mount"`.
5. **Recreation.** Fill the recreation table in your notes. Before and after each
   command, record the container id (`docker inspect -f '{{.Id}}' highrev-api-1 | cut -c1-12`,
   and the same for `highrev-mlflow-1`) and `loaded_at` from `/health`. The rows for
   your health-check and mount edits come from what `up` printed in E2 and step 4. Then:

   ```bash
   docker compose up -d api                              # nothing changed
   ADMIN_TOKEN=rotated docker compose up -d api          # a variable from your shell
   wait_api && reload                                   # with the usual token
   docker compose up -d api                              # back in the normal shell
   wait_api && reload
   ```

   For the job row, change `retries: 12` to `retries: 11` in the **`mlflow`** health
   check, save, and do *not* run `up`. Run the same job twice and read what Compose
   prints about `highrev-mlflow-1`:

   ```bash
   docker compose run --rm -T --no-deps project python -c 'print("job ran")'
   docker compose run --rm -T project python -c 'print("job ran")'
   ```

   Change `retries: 11` back to `12`, then `docker compose up -d mlflow` and
   `git status --short compose.yaml` (it must print nothing).

**Expected result:** before the repair, reload answers 409 with `reload refused:
FileNotFoundError: No /serving/current.json: nothing deployed yet` and
`still_serving: null`, although `ls serving` shows your pointer and model. An empty
folder you did not create appeared in your project when the API started; `.Mounts` shows
that folder as the source of `/serving`, and `ls -A /serving` in the container prints
nothing. `docker compose up` reported success throughout. After the repair, `up`
recreates `api` only (`mlflow` stays `Running`), `api` turns `(healthy)` within
seconds, and `/health` reports your version with `"ready":true`: the model loads at
startup, no reload needed. The `null` browser is answered with 200 and a probability.
Recreation table: no change → `api` kept; your health-check
and mount edits → recreated; `ADMIN_TOKEN=rotated` → recreated, and the next reload
is refused with 403; back in the normal shell → recreated again, reload 200; the job
with `--no-deps` → `mlflow` kept; without it → `Recreate … Healthy` for `mlflow` (the
instructor's run: 8 s), then once more when you restore the file. The API's
`loaded_at` changes at every recreation.

**Check:** why did `docker compose up` succeed with a mount that points nowhere useful?
What does Compose compare to decide on recreation? Why did a recreated API still serve
the same model? A scheduler or CI job that runs `docker compose run` with a different
environment from yours: what can it do to your running services? Readiness proves a
model is loaded; what does the `null` request show it does not prove, and which Lab 08
layer would notice such inputs?

**Failure and recovery:** reload answers 409 `Pointer names … but … holds …`: the
folder name and the version in its `lab07-model.json` differ; use `point` with the
version `v1` printed. `ls -A /serving` still empty after the repair: the edit was not
saved, or `up` was not run (`docker compose config | grep -A3 volumes`). 403 on reload:
`ADMIN_TOKEN` is still set in this terminal (`unset ADMIN_TOKEN`, then
`docker compose up -d api`).
**Checkpoint E3:** `api` healthy and serving your v1 from `./serving`; the
recreation table filled; `mlflow` back on the committed file. **Handoff:** commit
`compose.yaml` and your notes. `serving/` stays outside Git.

## L09-E4 — The monitoring cycle in containers

**Purpose:** run your Lab 08 monitoring window with every stage in a container, and
prove that the batches were scored with the model the API serves.
**Start:** E3 committed; API ready with v1; `mlflow` healthy.

`scripts/cycle.sh` runs one window: simulate and validate in a `project` job, score
in an `ag` job with the model the pointer names, record the window in MLflow with the
tracking job, then compare the served and the scored model. Each job is a
`docker compose run --rm -T --no-deps` container that is removed when it ends. The
tracking job ends by printing three lines `NAME=value` that the script evaluates.
Read the script before running it.

1. Run the clean window:

   ```bash
   bash scripts/cycle.sh none; echo "exit $?"
   ```

2. **Observe.** Which stage was last announced (`==>` lines), what is the exit code,
   and what does the last error line say? Open `http://127.0.0.1:5000`: is there a run
   in experiment `lab09-monitoring`?
3. **Investigate.** Run the tracking job alone, with its two output streams separated,
   and print stdout so that invisible and unusual characters show:

   ```bash
   docker compose run --rm -T --no-deps project python -m highrev.monitoring.track \
     --reports data/08_reporting/monitoring/lab09/none > /tmp/track.out 2> /tmp/track.err
   echo "exit $?"
   printf '%q\n' "$(cat /tmp/track.out)"
   cat /tmp/track.err
   ```

4. **Repair** `scripts/cycle.sh` so that `eval` receives only the job's `NAME=value`
   lines. Constraint: your repair follows the job's contract (lines that look like
   `NAME=value`), not the text of today's noise, so a new log line in the next MLflow
   version cannot break it again. Rerun the cycle; the stream already exists and is not
   simulated again.
5. **Verify.** Fill the identity table in your notes, then compare with Lab 08 and look
   for the results the removed containers left behind:

   ```bash
   cat serving/current.json; curl -s "$api/health"; echo
   head -3 data/08_reporting/monitoring/lab09/none/scores.csv
   diff <(cut -d, -f1-7 data/08_reporting/monitoring/none/scores.csv) \
        <(cut -d, -f1-7 data/08_reporting/monitoring/lab09/none/scores.csv) && echo "same scores as Lab 08"
   docker compose run --rm -T --no-deps -v "$run:/run:ro" project python -m highrev.monitoring validate \
     --comparison /run/comparison --stream data/05_serving/lab09/none --html 2026-10-10
   docker volume ls
   ```

   Open `data/08_reporting/monitoring/lab09/none/2026-10-10/drift.html` and, in the
   MLflow UI, the run's parameters and its `scores.csv` artifact.
6. **Check question, run it.** Point one job at `localhost` and read the error:

   ```bash
   docker compose run --rm -T --no-deps -e MLFLOW_TRACKING_URI=http://localhost:5000 \
     project python -m highrev.monitoring.track --reports data/08_reporting/monitoring/lab09/none
   ```

   Write incident row "E4".

**Expected result:** the first run stops after `==> Track the window in MLflow` with exit
127 and an error like `scripts/cycle.sh: line 50: $'\360\237\217\203': command not
found`; no identity check ran, yet the MLflow run *was* created. Run alone, the job
exits 0; `%q` shows MLflow's `View run …` and `View experiment …` lines (they start
with an emoji, the bytes in the error) on stdout before the three `NAME=value` lines;
stderr holds Compose's container lines (and, on the first run only, MLflow's line
about creating the experiment). After your repair the cycle exits 0 and
ends with `OK: served <v1> = scored <v1>` and an MLflow run id (the instructor's
repaired run took 10–15 s). The first seven columns of `scores.csv` equal your Lab 08
scores for the clean stream; `git_commit` names your current commit. If `diff` prints
lines, compare the values: differences in late decimals come from running Lab 08 on
another operating system or library build; a ROC AUC that differs in the second
decimal is an incident. The jobs read your project's parameters, so validation uses
your Lab 08 drift threshold; if `ip_address_country` is drifted on every clean day,
your Lab 08 threshold is not in the committed `conf/base/parameters.yml`. `drift.html`
is on your disk; the MLflow run is in volume `highrev_mlflow`. The `localhost` job
fails within seconds with `Failed to establish a new connection` to `localhost:5000`.

**Check:** which bug class is the exit-127 incident, and why did every stage before it
look fine? Why is matching the `View run` text a worse repair than yours? The job
containers are gone: where do the MLflow run, its `scores.csv` artifact and
`drift.html` live now, and what would have happened to a report written to `/tmp`
inside a job? What does `localhost` mean inside a container, and which name works
instead? The tracking URI fails at once only because `compose.yaml` sets
`MLFLOW_HTTP_REQUEST_MAX_RETRIES=0`; MLflow's default retries for minutes.

**Failure and recovery:** `The API is not ready`: E3 is not finished (`curl "$api/ready"`).
`MISMATCH: the API serves … but the batches were scored with …`: the check works;
the pointer changed between scoring and tracking; read `serving/current.json`, reload
or point back, rerun. `PermissionError` while scoring: your `ag` service lost its
`user: "0:0"` line (optional challenge C1). `No …/comparison`: `run` is not exported in
this terminal (Before class block). Your edit breaks the script (`syntax error`):
`git diff scripts/cycle.sh`, fix or `git checkout -- scripts/cycle.sh` and retry.
**Checkpoint E4:** the cycle ends with `OK: served = scored`; identity table and E4 row
written. **Handoff:** commit `scripts/cycle.sh` and your notes. Streams and reports stay
outside Git.

## L09-E5 — Deploy, verify, roll back

**Purpose:** change the served model independently of the image, prove which model
serves, and undo a deploy quickly.
**Start:** E4 committed; API serving v1.

**Version names and resume:** the commands below use `lab07-v2` for the new model
and `lab07-v3` for the deliberately missing model. Before running them, check
`ls serving/models` and your notes. The new version must differ from `$v1`. If
`lab07-v2` is already a completed version from this exercise, verify its
`lab07-model.json` and skip training. For a different new name, replace **every**
`lab07-v2` occurrence below, including the deploy command and expected identity.
Choose a missing-model name that is absent from `serving/models/` and replace every
`lab07-v3` occurrence if needed. Record both names in your notes and restore those
choices when reopening a terminal. Never overwrite a model folder to repeat E5.

1. Record the starting state in the E5 table: `/health`, the container id
   (`docker inspect -f '{{.Id}}' highrev-api-1 | cut -c1-12`) and
   `wc -l serving/predictions/*.jsonl`.
2. Produce a second version with your Lab 07 trainer, in the AutoGluon job container.
   It writes into your project's `serving/models/` through the project mount:

   ```bash
   docker compose run --rm -T --no-deps -v "$run:/run:ro" ag python -m lab07.train \
     --comparison /run/comparison --output ../serving/models/lab07-v2 --version lab07-v2 --seconds 60
   grep '"model_version"' serving/models/lab07-v2/lab07-model.json
   ```

   Run training once, following the version-name and resume checks above.
3. Deploy and verify by identity:

   ```bash
   point lab07-v2
   reload
   curl -s "$api/health"; echo
   curl -s -i -H 'Content-Type: application/json' -d "$row" "$api/predict" | grep -i x-model-version
   curl -s -H 'Content-Type: application/json' -d "$row" "$api/predict"; echo
   ```

4. Roll back, and measure it:

   ```bash
   time { point "$v1" && reload; }
   docker inspect -f '{{.Id}}' highrev-api-1 | cut -c1-12
   ```

5. A bad deploy: point at a version that does not exist, then look at what serves.

   ```bash
   point lab07-v3
   reload
   curl -s "$api/health"; echo
   curl -s -H 'Content-Type: application/json' -d "$row" "$api/predict"; echo
   point "$v1"
   reload
   ```

6. Persistence: stop and remove the containers, start them again, and compare.

   ```bash
   docker compose down
   docker compose up -d mlflow api && wait_api
   docker compose ps
   curl -s "$api/health"; echo
   wc -l serving/predictions/*.jsonl
   ```

   Check in the MLflow UI that the E4 run is still listed.

**Expected result:** training writes `lab07-v2` (the instructor's run: about 2 s). The
deploy answers 200 `"before":"<v1>","after":"lab07-v2"`; `/health` and the
`X-Model-Version` header say `lab07-v2`. The prediction may be exactly the same as
v1's: with the same data and a deterministic trainer, v2 can be the same model under a
new name. The rollback answers `"before":"lab07-v2","after":"<v1>"`; `time` reports
well under a second (instructor: 59 ms) and the container id is unchanged: no
rebuild, no recreation. The bad deploy answers 409 `reload refused: FileNotFoundError:
…/serving/models/lab07-v3/lab07-model.json` with `still_serving` your v1; `/predict`
still answers with v1, and `/health` keeps v1 and shows the refusal in `error`. After
`down` and `up` the containers are new, `/health` reports what the pointer names, the
prediction-log line count has not dropped, and the MLflow run is still there.

**Check:** why can the `/predict` values not tell you which model serves, and what can?
What did the rollback consist of, and what would it have cost if the model were
baked into the image? (Instructor measurements: rebuilding the Lab 07 image for a new
model took 48 s; even a code-only rebuild and redeploy of this API took 3.7 s with a
1.3 s outage.) Why does rollback depend on keeping v1's folder? What survived `down`,
and what would `docker compose down -v` have destroyed?

**Prevent, in one sentence for your notes:** after a refused deploy the bad pointer is
still on disk, and the next restart of the container (a crash, a reboot, a recreation
as in E3) would load it and come up without a model; restore the pointer at once, or
write it only after checking the new folder.

**Failure and recovery:** 409 `Pointer names lab07-v2 but … holds …`: you trained with a
different `--version`; `point` that version. Training refuses an existing output: pick
a new version name. `/health` after `up` reports no model and `error` mentions
`lab07-v3`: the bad pointer was left in place; `point "$v1"` and `reload`.
`docker compose up` reports that a port is already allocated: another container holds
8007 or 5000 (`docker ps`).
**Checkpoint E5:** v1 serving after `down`/`up`, E5 table filled. **Handoff:** commit
your notes. Keep `serving/` (both model folders, the pointer) on disk.

## L09-E6 — Acceptance

**Purpose:** decide, with evidence, whether this system is fit to be the base of the
next labs.
**Start:** E1–E5 evidence in your notes.

Work through the [checklist](09_containers/checklist.md). For every item, point to the
row of your notes that proves it; an item without evidence is not ticked. Then write
the acceptance decision at the end of your notes: approve or reject, the evidence, and
one risk that remains. Commit the notes and check the handoff:

```bash
git add notes/session-09.md && git commit -m "Lab 09: acceptance notes"
git status --short
git status --short --ignored serving data/05_serving | head
docker compose ps
```

**Expected result:** a clean working tree; `serving/` and the streams are listed as
ignored; `mlflow` and `api` healthy (right after a restart they show
`health: starting` for a few checks first). Repeat `docker compose ps` until both
verdicts are available; do not approve while either is still starting. If they do
not settle within two minutes, inspect the health-check output and service logs.

**Failure and recovery:** `git status` lists `serving/` or `data/05_serving/`: the
`.gitignore` lines from Before class are missing; add them and commit. A service is
`unhealthy`: go back to the exercise whose repair it depends on (E2 for the check, E3
for the mount) and compare `compose.yaml` with your committed repair.
**Checkpoint E6:** the lab's exit state. **Handoff:** Lab 10 starts from this commit,
the `./serving` folder with v1 deployed, and the `highrev_mlflow` volume; keep all
three.

## Optional challenges

After E6, on your committed system, try the [challenges](09_containers/challenges.md):
a job that cannot read its own data (C1), a health check that never succeeds (C2), and
an API that refuses to start without a model (C3). Each breaks one thing on purpose and
tells you how to restore it. They are not graded.

## Expected results and troubleshooting

| Check | Expected observation | What it does not prove |
|---|---|---|
| Setup | Both images built; `compose ok` | That the system works |
| E1 inventory | Four services and jobs; ports, users, mounts, state locations written down | That the configuration is correct |
| E2 health | Green status with a 503 prediction before; `(unhealthy)` without a model after the repair | That a loaded model accepts only valid inputs |
| E3 mount | 409 and an unexpected empty folder before; `(healthy)` with your v1 after; recreation table | That nothing else recreates your services |
| E4 cycle | Exit 127 before; `OK: served = scored` after; scores equal Lab 08; run and report outside the containers | That the scored model is a good model |
| E5 deploy | v2 then v1 by identity, same container; rollback well under a second; 409 keeps v1; state survives `down`/`up` | That the pointer is safe across a restart after a refused deploy |

| Symptom | First action |
| --- | --- |
| `C:/Program Files/Git/...` in an error, or `the working directory … is invalid` | `MSYS_NO_PATHCONV` is not set in this Git Bash terminal: run the Before class block. In PowerShell this does not happen |
| A mount that should hold files is empty, without an error | Check the host path in `compose.yaml` and `docker inspect -f '{{json .Mounts}}' <container>`; a missing host folder is created empty |
| `Bind for 127.0.0.1:8007 failed: port is already allocated` | Another container (often Lab 07's) holds the port: `docker ps`, then `docker stop <name>` |
| `Cannot connect to the Docker daemon` | Start Docker Desktop (or `sudo systemctl start docker`) and wait until it reports running |
| Linux only (not yet tested by the instructor): `/predict` answers 500 and `docker compose logs api` shows `PermissionError` under `/serving/predictions` | The API runs as uid 10001 and your `serving/` folder belongs to you: `mkdir -p serving/predictions && chmod a+rwx serving/predictions`, then retry |
| `Restarting (137)` and a log that stops at `Waiting for application startup` | The container runs out of memory: `docker inspect -f '{{.State.OOMKilled}}' <container>` while it restarts; raise Docker Desktop's memory or close programs |
| `mlflow` slow to become healthy, or the machine swaps | MLflow alone uses about 1.9 GB; check `docker stats --no-stream` and the memory line of the readiness check |
| `docker compose ps` shows nothing although the system ran | You are in another folder, or `COMPOSE_PROJECT_NAME` is set: `cd "$project"`, `unset COMPOSE_PROJECT_NAME` |
| Reload 403 | Wrong token, or `ADMIN_TOKEN` still exported from E3: `unset ADMIN_TOKEN`, `docker compose up -d api` |
| Reload 409 | Read `error`: a missing folder, a version mismatch, or an unloadable model; the old model still serves |
| Linux: files under `serving/models` or `data/` owned by root | `ag` runs as root; remove them with `docker compose run --rm -T --no-deps ag rm -rf <path relative to lab07/>` |
| A build fails while downloading | Network or registry problem: rerun the build; cached layers are kept |

## Exit checklist and next step

Your project now contains a containerized system with three configuration repairs
you can explain, a monitoring cycle that proves the scored model is the served model,
and notes with your inventory, evidence and incident table. `serving/` holds two
model versions and a pointer outside Git; MLflow holds your Lab 09 runs in its
volume. Lab 10 builds on this system: it puts the quality gate and the monitoring
checks into CI and registers AutoGluon versions, so the pointer you wrote by hand
today is derived from a registry instead. Keep the system and `serving/`; stop it with
`docker compose down` (never `-v`) when you do not need it.

## Homework L09-HW — What belongs in an image

Individual research outside your project repository; not graded.

1. `docker image history highrev-autogluon:local` and `docker image history highrev-lab07-api`
   (your Lab 07 image, model baked in). Which layers make up most of each image? How
   big is the model compared with the image? The instructor measured 1.71 GB and
   1.39 GB with a 4 MB model.
2. Read `lab07/Dockerfile`. Two lines make it rebuild far more than necessary: one
   makes every new commit reinstall the environment, one makes every new model copy
   the whole environment again (the instructor measured 61 s and 48 s; the Lab 09 image
   rebuilds in 6 s for a new commit and needs no rebuild for a new model). Find them, explain them with the layer
   rule from the Concepts, and propose a fix.
3. Build context: build once with `.dockerignore` and once without it (rename it
   temporarily; restore it afterwards), and compare the `transferring context` line of
   `docker compose --progress plain build api`. Without the file the whole project is
   sent to the builder, so that build can take a while. What would enter the build without it,
   and which of those files must never be in an image?

Reading: the Docker documentation on [build cache](https://docs.docker.com/build/cache/)
and [health checks](https://docs.docker.com/reference/dockerfile/#healthcheck), and the
Compose reference for [`depends_on`](https://docs.docker.com/reference/compose-file/services/#depends_on).
