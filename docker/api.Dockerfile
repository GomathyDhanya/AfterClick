FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY afterclick ./afterclick
COPY migrations ./migrations
COPY alembic.ini ./
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "uvicorn", "afterclick.api:app", "--host", "0.0.0.0", "--port", "8000"]
