FROM node:24-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv
WORKDIR /opt/validation
COPY pyproject.toml uv.lock ./
RUN uv python install 3.11 && uv sync --frozen --no-install-project
ENV PATH="/opt/validation/.venv/bin:${PATH}"
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN python -m playwright install --with-deps chromium
WORKDIR /workspace
CMD ["bash", "scripts/validate-container.sh"]
