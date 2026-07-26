FROM python:3.11-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# System deps for psycopg2, plus uv itself (from PyPI — reproducible installs
# straight from uv.lock). `libxml2-dev libxslt1-dev` стояли здесь ради `lxml`;
# он ушёл из зависимостей 2026-07-26 вместе с `duckduckgo-search` и
# `beautifulsoup4` — их тянул удалённый topic-pipeline, а импортов не осталось
# ни одного во всём дереве.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Install dependencies first (cached unless the lockfile changes); no dev tools.
# pyproject.toml / uv.lock live at the repo root (single project).
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

# App code (migrations + entrypoint included)
COPY backend/ .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# entrypoint.sh runs `alembic upgrade head` then execs uvicorn.
ENTRYPOINT ["/app/entrypoint.sh"]
