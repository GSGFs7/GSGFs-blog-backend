# AGENTS.md - GSGFs-blog-backend

## Project Overview

Django 5.2 + Django-Ninja backend for a personal blog with AI-powered search (vector embeddings), Celery tasks, PostgreSQL with pgvector, and two-factor authentication.

## Build/Lint/Test Commands

```bash
# Install dependencies
uv sync

# Run PostgreSQL and Redis
podman-compose up -d "blog-postgres" "blog-redis"

# Run development server
uv run manage.py runserver

# Run migrations
uv run manage.py makemigrations && uv run manage.py migrate

# Run all tests
uv run manage.py test

# Check code with ruff
ruff check

# Format code
ruff format .
```

## Code Style Guidelines

### Import Order

Standard library → third-party → local:

```python
# Standard library
import logging

# Third-party
from django.db import models
from ninja import Router

# Local
from api.models import Post
```

### Naming Conventions

**Models**: PascalCase for classes (`Post`, `Comment`), snake_case for fields (`created_at`)
**Routers**: snake_case for functions (`get_posts`, `create_post`)
**Schemas**: PascalCase with `Schema` suffix (`PostSchema`, `PostCardsSchema`)
**Variables**: snake_case (`post_id`, `CONFIDENCE`)
**Constants**: UPPER_SNAKE_CASE (`RESERVED_SLUGS`, `UPDATE_VNDB_INTERVAL`)

### Type Hints

Python 3.13+ type hints, import from `typing` when needed, use `PositiveInt` from pydantic for validation.

### Error Handling

```python
try:
    post = Post.objects.get(pk=post_id)
except Post.DoesNotExist:
    return 404, {"message": "Not found"}
except Exception as e:
    logging.error(e)
    return 500, {"message": "Internal Server Error"}
```

Use `@transaction.atomic` for database operations that need to be atomic.

### Django Patterns

**Models**: Inherit from `BaseModel` for `created_at`/`updated_at`, `abstract=True` for base classes, `db_index=True` for frequently queried fields
**Admin**: Create `ModelAdminForm`, use `readonly_fields`, add `list_display`/`list_filter`/`search_fields`
**API (Django-Ninja)**: Use `Router()`, return tuples `(status_code, response_dict)`, use `response={200: Schema, 404: MessageSchema}`, add `auth=TimeBaseAuth()` for authenticated endpoints
**Celery Tasks**: Use `@shared_task`, `.delay()` to queue, `task.get(timeout=1)` for sync execution in tests

### Testing

Use `TestCase` from `django.test`, `@override_settings` for test config, `CELERY_TASK_ALWAYS_EAGER=True` for sync tasks. Use `self.client.get()` for API testing, `assertContains()` for validation. Custom `QuietTestRunner` suppresses noisy logs.

### File Structure

```
api/
├── models.py          # Django models
├── schemas/           # Pydantic/Ninja schemas
    ├── post.py
    └── ...
├── routers/           # API endpoints
│   ├── post.py
│   ├── comment.py
│   └── ...
├── tasks.py           # Celery tasks
├── tests/             # Test files
│   ├── test_posts.py
│   ├── test_auth.py
│   └── runner.py      # QuietTestRunner
├── admin.py           # Django admin
├── auth.py            # Authentication
├── signals.py         # Django signals
└── utils.py           # Utility functions
```

### Database

PostgreSQL with pgvector, vector field: `embedding = VectorField(dimensions=768)`, use `CosineDistance` for similarity search, GIN indexes for full-text search with `SearchVectorField`.

### ML/Embeddings

Model: `google/embeddinggemma-300m` (default), embeddings stored in `Post.embedding`, generated asynchronously via Celery task `generate_post_embedding`, search uses cosine similarity with threshold `CONFIDENCE = 0.3`.

### Common Issues

1. **Test database errors**: Ensure test database created or use `DATABASE_URL`
2. **Celery tasks not running**: Set `CELERY_TASK_ALWAYS_EAGER=True` in tests
3. **Embedding generation fails**: Ensure model downloaded and `SENTENCE_TRANSFORMERS_HOME` set
4. **Reserved slug error**: Check `RESERVED_SLUGS` in `api/models.py`
5. **Import errors**: Run `ruff check --select I` to fix import order

### Key Files

- `pyproject.toml`: Dependencies, ruff config (line-length: 88, select: I,E,F)
- `blog/settings.py`: Django settings, includes Docker/K8s environment detection
- `api/models.py`: Database models with vector search support
- `api/schemas.py`: Pydantic/Ninja schemas
- `api/routers/`: API endpoints organized by resource
- `api/tasks.py`: Celery background tasks
- `api/tests/runner.py`: Custom `QuietTestRunner` to suppress noisy logs
- `api/tests/`: Test suite
- `scripts/`: Utility scripts
