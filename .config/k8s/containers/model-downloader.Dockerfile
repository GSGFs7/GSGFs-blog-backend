# syntax=docker/dockerfile:1
# Model downloader for init container

FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir -p /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends git

COPY pyproject.toml uv.lock ./

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN uv sync --frozen --no-install-project --no-cache

COPY scripts/download-model.py ./scripts/

ENV PATH="/app/.venv/bin:$PATH"

# avoid file sharing permission issue
RUN useradd -m -u 1000 user && \
    mkdir -p /models && \
    chown -R user:user /app /models

USER user

CMD ["python", "/app/scripts/download-model.py"]
