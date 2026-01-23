# AGENTS.md - GSGFs-blog-backend

> **Note**: This file is automatically maintained. If you notice any outdated information or missing commands, please update this file and update the last modified date below.

> **Last Modified**: 2026-01-23

## Project Overview
Django 5.2 + Django-Ninja backend for a personal blog with AI-powered search (vector embeddings), Celery tasks, and PostgreSQL with pgvector.

## Build/Lint/Test Commands

### Development
```bash
# Install dependencies
uv sync

# Run PostgreSQL and Redis
docker compose up -d "blog-db" "blog-redis"

# Run development server
./manage.py runserver

# Run migrations
./manage.py makemigrations && ./manage.py migrate
```

### Testing
```bash
# Run all tests
./manage.py test

# Run single test file
./manage.py test api.tests.test_posts

# Run single test class
./manage.py test api.tests.test_posts.TestPost

# Run single test method
./manage.py test api.tests.test_posts.TestPost.test_post_embedding_generation

# Run tests with verbose output
./manage.py test --verbosity 2

# Run tests with specific test runner (Django default)
./manage.py test api.tests.test_posts --testrunner django.test.runner.DiscoverRunner
```

### Linting & Formatting
```bash
# Check code with ruff
ruff check

# Fix auto-fixable issues
ruff check --fix

# Format code
ruff format .

# Check imports
ruff check --select I

# Run all checks
ruff check && ruff format --check
```

### Docker/Production
```bash
# Build Docker image
./scripts/docker-build.sh

# Export Docker image
./scripts/docker-export.sh

# Build with Podman
./scripts/podman-build.sh

# Export with Podman
./scripts/podman-export.sh
```

### Scripts
```bash
# Download ML models for embeddings
./scripts/download-model.py

# Regenerate all post embeddings
./scripts/regenerate_embeddings.py

# Backup database
./scripts/backup-db.sh

# Restore database
./scripts/restore-db.sh

# Upload files to R2
./scripts/upload.py
```

## Code Style Guidelines

### Import Order
Follow Django conventions with standard library → third-party → local imports:

```python
# Standard library
import logging
from datetime import datetime

# Third-party
from django.db import models
from ninja import Router
from pydantic import BaseModel

# Local
from api.models import Post
from api.schemas import PostSchema
```

### Naming Conventions

**Models (Django ORM):**
- PascalCase for model classes: `Post`, `Comment`, `Guest`
- snake_case for fields: `created_at`, `content_html`
- Related names: plural lowercase: `related_name="posts"`

**Views/Routers:**
- snake_case for functions: `get_posts`, `create_post`
- Descriptive names: `get_post_from_slug` not `get_post_by_slug`

**Schemas (Pydantic/Ninja):**
- PascalCase for classes: `PostSchema`, `PostCardsSchema`
- Use `Schema` suffix for clarity

**Variables:**
- snake_case: `post_id`, `query_embedding`, `CONFIDENCE`

**Constants:**
- UPPER_SNAKE_CASE: `RESERVED_SLUGS`, `UPDATE_VNDB_INTERVAL`

### Type Hints
- Use Python 3.13+ type hints
- Import from `typing` when needed: `from typing import Optional, List`
- Use `PositiveInt` from pydantic for validation
- Type Django fields explicitly: `models.CharField(max_length=50)`

### Error Handling
- Use specific exception handling:
```python
try:
    post = Post.objects.get(pk=post_id)
except Post.DoesNotExist:
    return 404, {"message": "Not found"}
except Exception as e:
    logging.error(e)
    return 500, {"message": "Internal Server Error"}
```

- Use `@transaction.atomic` for database operations that need to be atomic
- Log errors with `logging.error()` or `logging.warning()`

### Django-Specific Patterns

**Models:**
- Always inherit from `BaseModel` for `created_at` and `updated_at`
- Use `abstract = True` in Meta for base classes
- Use `db_index=True` for frequently queried fields
- Use `blank=True, null=True` for optional fields

**Admin:**
- Create `ModelAdminForm` for validation
- Use `readonly_fields` for auto-generated fields
- Add `list_display`, `list_filter`, `search_fields` for better UX

**API (Django-Ninja):**
- Use `Router()` for route organization
- Return tuples: `(status_code, response_dict)` or just model
- Use `response={200: Schema, 404: MessageSchema}` for type hints
- Add `auth=TimeBaseAuth()` for authenticated endpoints

**Celery Tasks:**
- Use `@shared_task` decorator
- Use `.delay()` to queue tasks
- Use `task.get(timeout=1)` for sync execution in tests

### Comments & Documentation
- Use English for code comments (project convention)
- Docstrings for public functions: `"""Generate embedding for a post."""`
- Avoid inline comments unless necessary

### Security
- Never log secrets or keys
- Use `@rate_limit` decorator for sensitive endpoints
- Validate user input in forms and serializers
- Use `SECURE_SSL_REDIRECT=False` only in tests

### Testing
- Use `TestCase` from `django.test`
- Use `@override_settings` for test-specific config
- Set `CELERY_TASK_ALWAYS_EAGER=True` for sync task execution
- Use `self.client.get()` for API testing
- Use `assertContains()` for response validation
- Test both success and error paths

### File Structure
```
api/
├── models.py          # Django models
├── schemas.py         # Pydantic/Ninja schemas
├── routers/           # API endpoints
│   ├── post.py
│   ├── comment.py
│   └── ...
├── tasks.py           # Celery tasks
├── tests/             # Test files
│   ├── test_posts.py
│   ├── test_auth.py
│   └── ...
├── admin.py           # Django admin
├── auth.py            # Authentication
├── signals.py         # Django signals
└── utils.py           # Utility functions
```

### Reserved Keywords
Avoid these slugs (defined in `api/models.py:169`):
- `posts`, `sitemap`, `search`, `post`, `all`, `query`, `ids`

### Environment Variables
Required in `.env`:
- `DJANGO_SECRET_KEY`
- `DATABASE_*` (or `DATABASE_URL`)
- `REDIS_HOST`, `REDIS_PORT`
- `API_KEY`
- `MODEL_NAME`, `SENTENCE_TRANSFORMERS_HOME`
- `HUGGINGFACE_HUB_TOKEN` (for model downloads)

### Database
- Using PostgreSQL with pgvector for vector embeddings
- Vector field: `embedding = VectorField(dimensions=768)`
- Use `CosineDistance` for similarity search

### ML/Embeddings
- Model: `google/embeddinggemma-300m` (default)
- Embeddings stored in `Post.embedding` field
- Generated asynchronously via Celery task `generate_post_embedding`
- Search uses cosine similarity with threshold `CONFIDENCE = 0.6`

### Common Issues & Solutions
1. **Test fails with "database does not exist"**: Ensure test database is created or use `DATABASE_URL`
2. **Celery tasks not running**: Set `CELERY_TASK_ALWAYS_EAGER=True` in tests
3. **Embedding generation fails**: Ensure model is downloaded and `SENTENCE_TRANSFORMERS_HOME` is set
4. **Reserved slug error**: Check `RESERVED_SLUGS` list in `api/models.py:169`
5. **Import errors**: Run `ruff check --select I` to fix import order

### Git Hooks
The project uses pre-commit hooks. Run before committing:
```bash
ruff check && ruff format .
```

### CI/CD
GitHub Actions run tests on:
- Python 3.14
- PostgreSQL with pgvector
- Redis
- Downloads ML models before tests

### Key Files Reference
- `pyproject.toml`: Project dependencies and tool config
- `blog/settings.py`: Django settings
- `api/models.py`: All database models
- `api/schemas.py`: All API schemas
- `api/routers/`: API endpoints organized by resource
- `api/tasks.py`: Celery background tasks
- `api/admin.py`: Django admin configuration
- `api/tests/`: Test suite
- `scripts/`: Utility scripts

### Quick Commands for Agents
```bash
# Run specific test
./manage.py test api.tests.test_posts.TestPost.test_post_embedding_generation

# Check code quality
ruff check && ruff format --check

# Fix issues
ruff check --fix && ruff format .

# Run single test file
./manage.py test api.tests.test_posts
```
