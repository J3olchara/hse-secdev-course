# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=8.14.1-2+deb13u2 \
    gcc=4:14.2.0-1 \
    libpq-dev=17.6-0+deb13u1 \
    libffi-dev=3.4.8-2 && \
    rm -rf /var/lib/apt/lists/*

ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-root --no-interaction --no-ansi --only main

COPY . .

FROM python:3.11-slim AS runtime

LABEL maintainer="wishlist-app" \
      version="1.0" \
      description="Wishlist API service"

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5=17.6-0+deb13u1 \
    curl=8.14.1-2+deb13u2 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

RUN chmod -R 755 /app && \
    chmod -R 500 /app/app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
