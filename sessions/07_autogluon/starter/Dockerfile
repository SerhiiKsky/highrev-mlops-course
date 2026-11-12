FROM python:3.11-slim
ARG SOURCE_REVISION=local
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY lab07 ./lab07
COPY model ./model
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH" MODEL_PATH=/app/model PORT=10000 SOURCE_REVISION=$SOURCE_REVISION
CMD ["sh", "-c", "exec uvicorn lab07.api:app --host 0.0.0.0 --port ${PORT}"]
