# AGENTS.md - GSGFs-blog-backend

## Core Tech Stack

Django 5.2 + Django-Ninja + pgvector + Celery + uv/ruff.

## CLI Workflow

```bash
# Setup: podman-compose up -d blog-postgres blog-redis
uv run manage.py migrate                # Database migrations
uv run manage.py test                   # Run tests
ruff check --fix && ruff format .       # Lint and format
```

## Project Map

- `api/models.py`: Database models (with Vector/Search fields).
- `api/routers/`: API endpoints and business logic (organized by resource).
- `api/schemas/`: Pydantic/Ninja schemas for request/response validation.
- `api/tasks.py`: Celery background tasks (embeddings, third-party sync).
- `api/auth.py`: Custom authentication logic (`TimeBaseAuth`).
- `api/tests/`: Comprehensive test suite and custom runner.
- `blog/settings.py`: Global Django configuration and environment detection.
- `scripts/`: Utility scripts for DB backup, model downloading, and deployment.

## Project-Specific Conventions

### API Development (api/routers/ & api/schemas/)

- **Auth**: Authenticated endpoints use `auth=TimeBaseAuth()`.
- **Responses**: Return as `(status_code, response_dict)`. Use Pydantic schemas for serialization.

### Async Tasks (api/tasks.py)

- Use `@shared_task`. In tests, use `task.apply()` or set `CELERY_TASK_ALWAYS_EAGER=True`.

### Testing (api/tests/)

- **Runner**: Uses custom `QuietTestRunner` (at `api/tests/runner.py`) to suppress noisy logs.
- **Config**: Ensure `@override_settings(SECURE_SSL_REDIRECT=False)` is set for any API tests.

## Documentation & Comments

- **Minimize Comments**: Write self-documenting code. Avoid adding new comments unless the logic is extremely complex.
- **Preserve Existing**: Do not modify or remove existing comments unless the underlying logic has changed and the comment is now incorrect.
- **No Docstrings**: Avoid adding new docstrings for internal methods or straightforward API endpoints.
