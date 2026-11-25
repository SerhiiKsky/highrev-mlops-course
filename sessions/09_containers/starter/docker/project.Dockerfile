# Project environment (Python 3.12, root uv.lock): Kedro, DVC, MLflow, Evidently.
# One image runs the MLflow server and every project-side stage. Stages run with the
# project directory mounted at /workspace, so code, conf, DVC pointer and reports are
# the ones on disk; the image only supplies the locked environment.
FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 && git config --system safe.directory '*'
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
WORKDIR /opt/highrev
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /mlflow /serving && chown appuser:appuser /mlflow /serving
ENV PATH="/opt/venv/bin:$PATH" PYTHONPATH=/workspace/src \
    KEDRO_DISABLE_TELEMETRY=1 PYTHONUTF8=1 MLFLOW_DISABLE_AGENT_HINT=1
WORKDIR /workspace
