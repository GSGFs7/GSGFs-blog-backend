# syntax=docker/dockerfile:1
# Use the '#syntax' to enable advanced features of BuildKit

FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir -p /app
WORKDIR /app

ARG MODEL_NAME
ARG SENTENCE_TRANSFORMERS_HOME
ENV MODEL_NAME=${MODEL_NAME}
ENV SENTENCE_TRANSFORMERS_HOME=${SENTENCE_TRANSFORMERS_HOME}

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

# Copy application code
COPY . .

# download model
# Use --mount=type=secret to safely mount the token
RUN --mount=type=secret,id=hf_token \
    export HUGGINGFACE_HUB_TOKEN=$(cat /run/secrets/hf_token) && \
    export MODEL_NAME=${MODEL_NAME} && \
    export SENTENCE_TRANSFORMERS_HOME=${SENTENCE_TRANSFORMERS_HOME} && \
    /app/.venv/bin/python /app/scripts/download-model.py

FROM python:3.14-slim

# supervisor: Manage multiple processes simultaneously
RUN apt-get update && apt-get install -y --no-install-recommends supervisor && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app
WORKDIR /app

RUN useradd -m user && \
    chown -R user /app

ARG MODEL_NAME
ARG SENTENCE_TRANSFORMERS_HOME
ENV MODEL_NAME=${MODEL_NAME}
ENV SENTENCE_TRANSFORMERS_HOME=${SENTENCE_TRANSFORMERS_HOME}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
ENV DOCKER_ENV="True"

# Copy the application from the builder
COPY --from=builder --chown=user:user /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# supervisor configuration
COPY --chown=root:root supervisord.conf /etc/supervisor/supervisord.conf

# supervisor log directory
RUN mkdir -p /var/log/supervisor && \
    chown -R user /var/log/supervisor

# collect static
RUN python manage.py collectstatic --noinput

# supervisor needs to run as root
# USER user 

EXPOSE 8000

# CMD [ "gunicorn", "-c", "gunicorn.conf.py", "blog.wsgi:application" ]
CMD [ "supervisord" , "-c", "/etc/supervisor/supervisord.conf" ]


# https://www.docker.com/blog/how-to-dockerize-django-app/
