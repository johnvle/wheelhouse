# Backend Agent Guide

## Project Structure
- `app/config.py` — pydantic-settings `Settings` with `get_settings()` + `@lru_cache`
- `app/database.py` — SQLAlchemy `Base`, `SessionLocal`, `get_db()` dependency
- `app/models/` — SQLAlchemy 2.0 ORM models (Account, Position)
- `app/schemas/` — Pydantic v2 schemas (TODO)
- `app/routers/` — FastAPI route handlers (TODO)
- `app/services/` — Business logic (TODO)
- `alembic/versions/` — Manual revision IDs (0002, 0003, ...)
- `tests/` — pytest tests; `conftest.py` sets dummy env vars

## Patterns
- **Models**: Use `Mapped[]` + `mapped_column()` (SQLAlchemy 2.0 declarative)
- **Cross-schema FKs**: `user_id` FK to `auth.users.id` is in migrations only, NOT in ORM models
- **Relationships**: Use `TYPE_CHECKING` guard for circular imports between related models
- **Test models**: Use `sqlalchemy.inspect(Model)` for structural assertions (no live DB needed)
- **Test env**: `conftest.py` sets dummy env vars before app module imports
- **Migrations**: `sa.text()` for `server_default`, `sa.ARRAY(sa.Text())` for `text[]`
