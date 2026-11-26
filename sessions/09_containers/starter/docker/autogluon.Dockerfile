# AutoGluon environment (Python 3.11, lab07/uv.lock): training, scoring, comparison and
# the live prediction API. The API runs the baked lab07 code as a non-root user and
# reads its model from the mounted serving folder; batch stages run the same image as root with
# the project mounted at /workspace (working directory /workspace/lab07).
FROM python:3.11-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 && git config --system safe.directory '*'
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
WORKDIR /app
COPY lab07/pyproject.toml lab07/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY lab07/lab07 ./lab07
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /serving && chown appuser:appuser /serving
ARG SOURCE_REVISION=local
ENV PATH="/opt/venv/bin:$PATH" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
    SERVING_DIR=/serving PORT=10000 SOURCE_REVISION=$SOURCE_REVISION
USER appuser
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn lab07.live_api:app --host 0.0.0.0 --port ${PORT}"]
