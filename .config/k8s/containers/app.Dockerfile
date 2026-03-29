# syntax=docker/dockerfile:1
# Base stage: Install dependencies and sync code
FROM archlinux:latest AS base

WORKDIR /app

# Unified environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    DOCKER_ENV="True" \
    PATH="/app/.venv/bin:/usr/bin/vendor_perl:$PATH"

# Install system dependencies and create user
RUN pacman-key --init && \
    pacman-key --populate archlinux && \
    pacman -Syu --noconfirm uv perl-image-exiftool git && \
    useradd -m -u 1000 user && \
    chown user /app

USER user

# Pre-install Python dependencies
COPY --chown=user:user pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-project --no-cache

# Copy project files and collect static
COPY --chown=user:user . .
#RUN uv run manage.py collectstatic --noinput

# --- Target: Django ---
FROM base AS django
EXPOSE 8000
CMD [ "gunicorn", "-c", "gunicorn.conf.py", "blog.asgi:application" ]

# --- Target: Celery Worker ---
FROM base AS worker
CMD [ "celery", "-A", "blog", "worker", "--loglevel=info", "--concurrency=1" ]

# --- Target: Celery Beat ---
FROM base AS beat
CMD [ "celery", "-A", "blog", "beat", "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler" ]

# --- Target: Model Downloader ---
FROM base AS downloader
CMD ["python", "/app/scripts/download-model.py"]
