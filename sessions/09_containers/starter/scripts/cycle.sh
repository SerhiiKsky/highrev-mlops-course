#!/usr/bin/env bash
# One Lab 08 monitoring window, every stage in a container. Run from the project root in
# Bash (Git Bash on Windows) with MLflow and the API up and the API ready:
#
#   run=/path/to/your-lab06-run bash scripts/cycle.sh [INCIDENT]
#
# INCIDENT is a Lab 08 simulator incident (default none). Stages:
#   1 simulate + validate  project job   data/05_serving/lab09/<incident>,
#                                         data/08_reporting/monitoring/lab09/<incident>
#   2 score                ag job        the model the serving pointer names
#   3 track                project job   MLflow run; which model was served and scored
#   4 identity check       this script   served model == scored model, or exit 1
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
export MSYS_NO_PATHCONV=1   # Git Bash: keep /serving/... and /run/... as typed

incident=${1:-none}
: "${run:?set run=/path/to/your-lab06-run (the folder that holds comparison/)}"
[[ -d "$run/comparison" ]] || { echo "No $run/comparison: check run=" >&2; exit 1; }
stream="data/05_serving/lab09/$incident"
reports="data/08_reporting/monitoring/lab09/$incident"

step() { printf '\n==> %s\n' "$*" >&2; }
# --no-deps: MLflow is already running; a job must never recreate a service.
P() { docker compose run --rm -T --no-deps -v "$run:/run:ro" project "$@"; }
AG() { docker compose run --rm -T --no-deps ag "$@"; }

curl -fsS -m 5 http://127.0.0.1:8007/ready >/dev/null \
    || { echo "The API is not ready (curl http://127.0.0.1:8007/ready): deploy a model first." >&2; exit 1; }
model_path=$(sed -n 's/.*"path": *"\([^"]*\)".*/\1/p' serving/current.json)
[[ -n "$model_path" ]] || { echo "serving/current.json names no model path" >&2; exit 1; }

if [[ -d "$stream" ]]; then
    step "Stream $stream exists: not simulated again"
else
    step "Simulate serving batches (incident $incident)"
    P python -m highrev.monitoring simulate --comparison /run/comparison \
        --incident "$incident" --out data/05_serving/lab09
fi
step "Validate: schema and drift"
P python -m highrev.monitoring validate --comparison /run/comparison --stream "$stream"

step "Score with the served model ($model_path)"
AG python -m lab07.score_batches --model "/serving/$model_path" \
    --stream "../$stream" --reports "../$reports"

step "Track the window in MLflow"
eval "$(P python -m highrev.monitoring.track --reports "$reports")"

step "Identity check"
echo "MLflow run $MLFLOW_RUN_ID: http://127.0.0.1:5000/#/experiments"
if [[ "$SERVED_MODEL" == "$SCORED_MODEL" ]]; then
    echo "OK: served $SERVED_MODEL = scored $SCORED_MODEL"
else
    echo "MISMATCH: the API serves $SERVED_MODEL but the batches were scored with $SCORED_MODEL" >&2
    exit 1
fi
