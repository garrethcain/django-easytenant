# django-easyshard

JWT-driven database-per-tenant sharding for Django.

Route every request to the correct database by extracting a `shard_id` from JWT tokens (or any source), resolving it to a Django database alias, and directing the ORM through a database router — all transparently.

Designed as a companion to [django-easyjwt](https://github.com/garrethcain/django-easyjwt) but works with **any** JWT system or extraction strategy.

---

## Features

- **Database-per-tenant routing** — each request's data goes to the right shard, automatically.
- **Pluggable shard ID extraction** — JWT, headers, sessions, admin query params, or your own custom extractor.
- **Manual shard assignment** — users are assigned to shards, enabling tiered infrastructure (trial users share a DB, enterprise get dedicated instances).
- **Two deployment modes**:
  - `local` — monolith reads `ShardConfig` from its own `default` database.
  - `remote` — microservice fetches shard configs from an auth service via HTTP with TTL caching.
- **Encrypted credentials** — database passwords encrypted at rest with Fernet (cryptography library).
- **Dynamic shard discovery** — add/remove shards at runtime via model, management command, or HTTP endpoint.
- **Admin support** — browse shard data with `?shard=` query parameter.
- **Composable** — works alongside schema-level tenancy libraries like `django-tenants`.

---

## Installation

```bash
uv add django-easyshard

# For JWT extraction (default):
uv add "django-easyshard[jwt]"

# For remote/microservice mode:
uv add "django-easyshard[remote]"

# For development (from source):
git clone https://github.com/garrethcain/django-easyshard
cd django-easyshard
uv sync --extra dev
```

---

## Quick Start (Monolith)

### 1. Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "easyshard",
]
```

### 2. Configure databases

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "auth_db",
        ...
    },
    "shard_trial": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shard_trial",
        ...
    },
    "shard_enterprise": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shard_enterprise",
        ...
    },
}

DATABASE_ROUTERS = ["easyshard.routers.ShardRouter"]
```

### 3. Configure settings

```python
EASY_SHARD = {
    "CONFIG_MODE": "local",
    "ID_EXTRACTOR": "easyshard.extractors.JWTShardExtractor",
    "ID_JWT_CLAIM": "shard_id",
    "ENCRYPTION_KEY": "your-fernet-key",  # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}
```

> **Note**: JWT verification defaults to `HS256` using Django's `SECRET_KEY` — the same defaults as django-easyjwt. No extra configuration needed unless you've overridden `SIGNING_KEY` in your `EASY_JWT` settings.

### 4. Add middleware

```python
MIDDLEWARE = [
    ...
    "easyshard.middleware.ShardMiddleware",
]
```

### 5. Add `shard_id` to your User model

```python
from django.contrib.auth.models import AbstractUser
from easyshard.models import ShardUserMixin

class User(ShardUserMixin, AbstractUser):
    pass
```

### 6. Create ShardConfig entries

```python
from easyshard.models import ShardConfig

ShardConfig.objects.create(
    shard_id="trial",
    db_alias="shard_trial",
    name="shard_trial",
    host="localhost",
    port=5432,
    user="app",
    password="db-password",  # encrypted at rest
)

ShardConfig.objects.create(
    shard_id="enterprise",
    db_alias="shard_enterprise",
    name="shard_enterprise",
    host="localhost",
    port=5432,
    user="app",
    password="db-password",
)
```

### 7. Issue JWTs with `shard_id` claim

```json
{
  "user_id": 42,
  "shard_id": "enterprise",
  "exp": 1700000000
}
```

That's it. Every request with a valid JWT now routes automatically to the correct database.

---

## Deployment Modes

### Local Mode (Monolith)

A single Django deployment managing all shard databases.

```python
EASY_SHARD = {
    "CONFIG_MODE": "local",
}
```

`ShardConfig` rows live on the `default` database. The connection manager loads them on first access and injects connection details into Django's `connections.settings` at runtime.

### Remote Mode (Microservice)

Shard databases are only accessible from worker services. The auth service hosts `ShardConfig` and exposes an API endpoint.

**Auth service:**

```python
EASY_SHARD = {
    "CONFIG_MODE": "local",
    "SERVICE_TOKEN": "shared-service-token",
}
```

Include the API URLs:

```python
# urls.py
urlpatterns = [
    path("", include("easyshard.urls")),
]
```

This exposes:

- `GET /shard-config/{shard_id}/` — returns a single shard's connection config (password re-encrypted for transit).
- `POST /shards/reload/` — triggers a reload of shard configs (requires `X-Shard-Reload-Secret` header).

**Worker service:**

```python
EASY_SHARD = {
    "CONFIG_MODE": "remote",
    "REMOTE_SHARD_CONFIG_URL": "https://auth.example.com",
    "REMOTE_SHARD_CONFIG_PATH": "/shard-config/",
    "SERVICE_TOKEN": "shared-service-token",
    "ENCRYPTION_KEY": "shared-fernet-key",
    "CACHE_TTL": 300,  # seconds
}
```

On first request for a shard, the worker fetches the config from the auth service, decrypts the password, and injects the connection into Django. The config is cached for `CACHE_TTL` seconds.

---

## Shard ID Extraction

The middleware delegates to a configurable extractor. Override `ID_EXTRACTOR` to change the strategy:

### JWT (default)

```python
EASY_SHARD = {
    "ID_EXTRACTOR": "easyshard.extractors.JWTShardExtractor",
    "ID_JWT_CLAIM": "shard_id",
    "MIDDLEWARE_VERIFY_TOKEN": True,  # verify JWT signatures (default: True)
}
```

Uses `HS256` and `SECRET_KEY` by default — matching django-easyjwt's defaults. Override `JWT_SIGNING_KEY` or `JWT_ALGORITHM` only if you've customized those in your JWT configuration.

**Using django-easyjwt with a custom signing key?** Subclass to read from easyjwt's settings:

```python
from easyshard.extractors import JWTShardExtractor

class EasyJWTShardExtractor(JWTShardExtractor):
    def get_signing_key(self):
        from easyjwt_auth.settings import api_settings
        return api_settings.SIGNING_KEY

    def get_algorithm(self):
        from easyjwt_auth.settings import api_settings
        return api_settings.ALGORITHM
```

```python
EASY_SHARD = {
    "ID_EXTRACTOR": "myapp.extractors.EasyJWTShardExtractor",
}
```

### HTTP Header

```python
EASY_SHARD = {
    "ID_EXTRACTOR": "easyshard.extractors.HeaderShardExtractor",
    "ID_HEADER_NAME": "X-Shard-Id",
}
```

### Session

```python
EASY_SHARD = {
    "ID_EXTRACTOR": "easyshard.extractors.SessionShardExtractor",
}
```

### Custom

```python
from easyshard.extractors import BaseShardExtractor

class TenantShardExtractor(BaseShardExtractor):
    def extract(self, request):
        return request.tenant.shard_id
```

```python
EASY_SHARD = {
    "ID_EXTRACTOR": "myapp.extractors.TenantShardExtractor",
}
```

---

## How Routing Works

| Component            | Behavior                                                                                                          |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `ShardMiddleware`    | Extracts `shard_id` from each request, sets it in a `ContextVar`. Clears after response.                          |
| `ShardRouter`        | Routes all models (except `easyshard` app) to the shard DB when context is active. Routes to `default` otherwise. |
| `connection_manager` | Resolves `shard_id` → Django database alias. Injects connection params into `connections.settings`.               |
| `ShardConfig` model  | Always routes to `default`. Stores encrypted credentials.                                                         |

**`allow_relation`** always returns `True` — every shard contains the full schema, so all related objects are always co-located.

**Missing shard** — when the middleware sets a `shard_id` that has no `ShardConfig`, `ShardNotConfiguredError` is raised, resulting in an HTTP 500.

---

## Admin Integration

The admin supports a `?shard=` query parameter for browsing data on specific shards:

```
/admin/blog/blogpost/?shard=trial
/admin/blog/blogpost/?shard=enterprise
```

This works because `AdminShardExtractor` is a fallback in the middleware — if the primary extractor returns `None`, the query param is checked.

---

## Management Commands

```bash
# Reload shard configs from the database
uv run python manage.py reload_shards
```

Shard configs also auto-reload when `ShardConfig` records are saved or deleted (via Django signals).

---

## Settings Reference

All settings live under the `EASY_SHARD` dictionary.

| Setting                    | Default                                   | Description                                         |
| -------------------------- | ----------------------------------------- | --------------------------------------------------- |
| `ID_EXTRACTOR`             | `easyshard.extractors.JWTShardExtractor`  | Import path to shard ID extractor class.            |
| `ID_JWT_CLAIM`             | `shard_id`                                | JWT claim name containing the shard ID.             |
| `ID_HEADER_NAME`           | `X-Shard-Id`                              | Header name for `HeaderShardExtractor`.             |
| `CONFIG_MODE`              | `local`                                   | `local` (monolith) or `remote` (microservice).      |
| `DB_RESOLVER`              | `easyshard.connection_manager.resolve_db` | Callable that maps `shard_id` → database alias.     |
| `MIDDLEWARE_VERIFY_TOKEN`  | `True`                                    | Whether to verify JWT signatures in the middleware. |
| `JWT_ALGORITHM`            | `HS256`                                   | JWT algorithm for verification.                     |
| `JWT_SIGNING_KEY`          | `None` (falls back to `SECRET_KEY`)       | Key for JWT verification.                           |
| `ENCRYPTION_KEY`           | `None` (derives from `SECRET_KEY`)        | Fernet key for encrypting credentials.              |
| `RELOAD_SECRET`            | `None`                                    | Secret for the `/shards/reload/` HTTP endpoint.     |
| `CACHE_TTL`                | `300`                                     | Cache TTL in seconds (remote mode only).            |
| `SERVICE_TOKEN`            | `None`                                    | Bearer token for auth service API (remote mode).    |
| `REMOTE_SHARD_CONFIG_URL`  | `None`                                    | Base URL of auth service (remote mode).             |
| `REMOTE_SHARD_CONFIG_PATH` | `/shard-config/`                          | Path to shard config API (remote mode).             |
| `ADMIN_SHARD_PARAM`        | `shard`                                   | Query parameter name for admin shard selection.     |

---

## Composing with Schema-Level Tenancy

`django-easyshard` operates at the **database connection** layer. Schema-level libraries like `django-tenants` operate at the **schema/search_path** layer. They can be composed:

```python
# Each tenant gets their own PostgreSQL schema within a shard database.
# django-easyshard routes to the correct database instance.
# django-tenants sets the search_path within that database.
```

---

## Examples

See [`examples/monolith/`](examples/monolith/) for a complete working example with 3 databases, a custom User model, and BlogPost model.

---

## License

MIT
