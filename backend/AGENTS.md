# Backend Agent Guide

## Project Structure
- `app/config.py` — pydantic-settings `Settings` with `get_settings()` + `@lru_cache`
- `app/database.py` — SQLAlchemy `Base`, `SessionLocal`, `get_db()` dependency
- `app/models/` — SQLAlchemy 2.0 ORM models (Account, Position)
- `app/auth.py` — JWT middleware (`JWTAuthMiddleware`) + `get_current_user` dependency
- `app/schemas/` — Pydantic v2 schemas (enums.py, account.py, position.py)
- `app/routers/` — FastAPI route handlers (accounts.py, positions.py)
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
- **Auth**: `JWTAuthMiddleware` verifies Supabase JWT (HS256) on all requests except public paths
- **Auth dependency**: `get_current_user` returns `UUID` from `request.state.user_id`
- **Auth tests**: Register test-only routes at module level; use `_make_token()` helper to create test JWTs
- **Routers**: `APIRouter(prefix="/api/v1/<resource>")`, wired via `app.include_router()` in main.py
- **Router tests**: Use `dependency_overrides[get_db]` with mock DB; `_FakeQuery` for chaining `.filter().first()`/`.all()`
- **Enum storage**: Use `.value` when setting enum fields on ORM models (e.g., `body.type.value`)
- **Account ownership**: Validate `account_id` belongs to user before creating positions (return 400 if not)
