# syntax=docker/dockerfile:1
# Celery Beat standalone image (for k3s deployment)

FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir -p /app
WORKDIR /app

# no .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# no output buffer
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends git

# Install dependencies
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-cache

COPY . .

FROM python:3.14-slim

RUN mkdir -p /app
WORKDIR /app

RUN useradd -m -u 1000 user && \
    chown -R user /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV="True"

# Copy the application from the builder
COPY --from=builder --chown=user:user /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

USER user

CMD [ "celery", "-A", "blog", "beat", "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler" ]
