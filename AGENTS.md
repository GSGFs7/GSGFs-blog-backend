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

### Models & Database (api/models.py)
- **Base Class**: Always inherit from `BaseModel` (provides `created_at`/`updated_at`).
- **Vector Search**: Use pgvector `VectorField(dimensions=768)`. Default similarity: `CosineDistance`.
- **Full-Text Search**: Configure GIN indexes on `SearchVectorField`.

### API Development (api/routers/ & api/schemas/)
- **Auth**: Authenticated endpoints use `auth=TimeBaseAuth()`.
- **Responses**: Return as `(status_code, response_dict)`. Use Pydantic schemas for serialization.

### Async Tasks (api/tasks.py)
- Use `@shared_task`. In tests, use `task.apply()` or set `CELERY_TASK_ALWAYS_EAGER=True`.

### Testing (api/tests/)
- **Runner**: Uses custom `QuietTestRunner` (at `api/tests/runner.py`) to suppress noisy logs.
- **Config**: Ensure `DATABASE_URL` is set for integration tests.

## Documentation & Comments
- **Minimize Comments**: Write self-documenting code. Avoid adding new comments unless the logic is extremely complex.
- **Preserve Existing**: Do not modify or remove existing comments unless the underlying logic has changed and the comment is now incorrect.
- **No Docstrings**: Avoid adding new docstrings for internal methods or straightforward API endpoints.

## Troubleshooting
1. **Vector Models**: If embeddings fail, ensure `SENTENCE_TRANSFORMERS_HOME` is set or run `scripts/download-model.py`.
2. **Postgres Extensions**: Ensure `pgvector` extension is enabled (see migration `0042_enable_vector_extension.py`).
3. **Env Detection**: `blog/settings.py` auto-detects Docker/K8s to adjust environment settings.
