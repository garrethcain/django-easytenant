# django-easytenant

JWT-driven database-per-tenant routing for Django.

Route every request to the correct database by extracting a `tenant_id` from JWT tokens (or any source), resolving it to a Django database alias, and directing the ORM through a database router — all transparently.

Designed as a companion to [django-easyjwt](https://github.com/garrethcain/django-easyjwt) but works with **any** JWT system or extraction strategy.

---

## Features

- **Database-per-tenant routing** — each request's data goes to the right tenant, automatically.
- **Pluggable tenant ID extraction** — JWT, headers, sessions, admin query params, or your own custom extractor.
- **Manual tenant assignment** — users are assigned to tenants, enabling tiered infrastructure (trial users share a DB, enterprise get dedicated instances).
- **Two deployment modes**:
  - `local` — monolith reads `TenantConfig` from its own `default` database.
  - `remote` — microservice fetches tenant configs from an auth service via HTTP with TTL caching.
- **Encrypted credentials** — database passwords encrypted at rest with Fernet (cryptography library).
- **Dynamic tenant discovery** — add/remove tenants at runtime via model, management command, or HTTP endpoint.
- **Admin support** — browse tenant data with `?tenant=` query parameter.
- **Composable** — works alongside schema-level tenancy libraries like `django-tenants`.

---

## Installation

```bash
uv add django-easytenant

# For JWT extraction (default):
uv add "django-easytenant[jwt]"

# For remote/microservice mode:
uv add "django-easytenant[remote]"

# For development (from source):
git clone https://github.com/garrethcain/django-easytenant
cd django-easytenant
uv sync --extra dev
```

---

## Quick Start (Monolith)

### 1. Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "easytenant",
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
    "tenant_trial": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "tenant_trial",
        ...
    },
    "tenant_enterprise": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "tenant_enterprise",
        ...
    },
}

DATABASE_ROUTERS = ["easytenant.routers.TenantRouter"]
```

### 3. Configure settings

```python
EASY_TENANT = {
    "CONFIG_MODE": "local",
    "ID_EXTRACTOR": "easytenant.extractors.JWTTenantExtractor",
    "ID_JWT_CLAIM": "tenant_id",
    "ENCRYPTION_KEY": "your-fernet-key",  # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}
```

> **Note**: JWT verification defaults to `HS256` using Django's `SECRET_KEY` — the same defaults as django-easyjwt. No extra configuration needed unless you've overridden `SIGNING_KEY` in your `EASY_JWT` settings.

### 4. Add middleware

```python
MIDDLEWARE = [
    ...
    "easytenant.middleware.TenantMiddleware",
]
```

### 5. Add `tenant_id` to your User model

```python
from django.contrib.auth.models import AbstractUser
from easytenant.models import TenantUserMixin

class User(TenantUserMixin, AbstractUser):
    pass
```

### 6. Create TenantConfig entries

```python
from easytenant.models import TenantConfig

TenantConfig.objects.create(
    tenant_id="trial",
    db_alias="tenant_trial",
    name="tenant_trial",
    host="localhost",
    port=5432,
    user="app",
    password="db-password",  # encrypted at rest
)

TenantConfig.objects.create(
    tenant_id="enterprise",
    db_alias="tenant_enterprise",
    name="tenant_enterprise",
    host="localhost",
    port=5432,
    user="app",
    password="db-password",
)
```

### 7. Issue JWTs with `tenant_id` claim

```json
{
  "user_id": 42,
  "tenant_id": "enterprise",
  "exp": 1700000000
}
```

That's it. Every request with a valid JWT now routes automatically to the correct database.

---

## Deployment Modes

### Local Mode (Monolith)

A single Django deployment managing all tenant databases.

```python
EASY_TENANT = {
    "CONFIG_MODE": "local",
}
```

`TenantConfig` rows live on the `default` database. The connection manager loads them on first access and injects connection details into Django's `connections.settings` at runtime.

### Remote Mode (Microservice)

Tenant databases are only accessible from worker services. The auth service hosts `TenantConfig` and exposes an API endpoint.

**Auth service:**

```python
EASY_TENANT = {
    "CONFIG_MODE": "local",
    "SERVICE_TOKEN": "shared-service-token",
}
```

Include the API URLs:

```python
# urls.py
urlpatterns = [
    path("", include("easytenant.urls")),
]
```

This exposes:

- `GET /tenant-config/{tenant_id}/` — returns a single tenant's connection config (password re-encrypted for transit).
- `POST /tenants/reload/` — triggers a reload of tenant configs (requires `X-Tenant-Reload-Secret` header).

**Worker service:**

```python
EASY_TENANT = {
    "CONFIG_MODE": "remote",
    "REMOTE_TENANT_CONFIG_URL": "https://auth.example.com",
    "REMOTE_TENANT_CONFIG_PATH": "/tenant-config/",
    "SERVICE_TOKEN": "shared-service-token",
    "ENCRYPTION_KEY": "shared-fernet-key",
    "CACHE_TTL": 300,  # seconds
}
```

On first request for a tenant, the worker fetches the config from the auth service, decrypts the password, and injects the connection into Django. The config is cached for `CACHE_TTL` seconds.

---

## Tenant ID Extraction

The middleware delegates to a configurable extractor. Override `ID_EXTRACTOR` to change the strategy:

### JWT (default)

```python
EASY_TENANT = {
    "ID_EXTRACTOR": "easytenant.extractors.JWTTenantExtractor",
    "ID_JWT_CLAIM": "tenant_id",
    "MIDDLEWARE_VERIFY_TOKEN": True,  # verify JWT signatures (default: True)
}
```

Uses `HS256` and `SECRET_KEY` by default — matching django-easyjwt's defaults. Override `JWT_SIGNING_KEY` or `JWT_ALGORITHM` only if you've customized those in your JWT configuration.

**Using django-easyjwt with a custom signing key?** Subclass to read from easyjwt's settings:

```python
from easytenant.extractors import JWTTenantExtractor

class EasyJWTTenantExtractor(JWTTenantExtractor):
    def get_signing_key(self):
        from easyjwt_auth.settings import api_settings
        return api_settings.SIGNING_KEY

    def get_algorithm(self):
        from easyjwt_auth.settings import api_settings
        return api_settings.ALGORITHM
```

```python
EASY_TENANT = {
    "ID_EXTRACTOR": "myapp.extractors.EasyJWTTenantExtractor",
}
```

### HTTP Header

```python
EASY_TENANT = {
    "ID_EXTRACTOR": "easytenant.extractors.HeaderTenantExtractor",
    "ID_HEADER_NAME": "X-Tenant-Id",
}
```

### Session

```python
EASY_TENANT = {
    "ID_EXTRACTOR": "easytenant.extractors.SessionTenantExtractor",
}
```

### Custom

```python
from easytenant.extractors import BaseTenantExtractor

class CustomTenantExtractor(BaseTenantExtractor):
    def extract(self, request):
        return request.tenant.tenant_id
```

```python
EASY_TENANT = {
    "ID_EXTRACTOR": "myapp.extractors.CustomTenantExtractor",
}
```

---

## How Routing Works

| Component            | Behavior                                                                                                          |
| -------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `TenantMiddleware`    | Extracts `tenant_id` from each request, sets it in a `ContextVar`. Clears after response.                          |
| `TenantRouter`        | Routes all models (except `easytenant` app) to the tenant DB when context is active. Routes to `default` otherwise. |
| `connection_manager` | Resolves `tenant_id` → Django database alias. Injects connection params into `connections.settings`.               |
| `TenantConfig` model  | Always routes to `default`. Stores encrypted credentials.                                                         |

**`allow_relation`** always returns `True` — every tenant contains the full schema, so all related objects are always co-located.

**Missing tenant** — when the middleware sets a `tenant_id` that has no `TenantConfig`, `TenantNotConfiguredError` is raised, resulting in an HTTP 500.

---

## Admin Integration

The admin supports a `?tenant=` query parameter for browsing data on specific tenants:

```
/admin/blog/blogpost/?tenant=trial
/admin/blog/blogpost/?tenant=enterprise
```

This works because `AdminTenantExtractor` is a fallback in the middleware — if the primary extractor returns `None`, the query param is checked.

---

## Management Commands

```bash
# Reload tenant configs from the database
uv run python manage.py reload_tenants
```

Tenant configs also auto-reload when `TenantConfig` records are saved or deleted (via Django signals).

---

## Settings Reference

All settings live under the `EASY_TENANT` dictionary.

| Setting                    | Default                                   | Description                                         |
| -------------------------- | ----------------------------------------- | --------------------------------------------------- |
| `ID_EXTRACTOR`             | `easytenant.extractors.JWTTenantExtractor`  | Import path to tenant ID extractor class.            |
| `ID_JWT_CLAIM`             | `tenant_id`                                | JWT claim name containing the tenant ID.             |
| `ID_HEADER_NAME`           | `X-Tenant-Id`                              | Header name for `HeaderTenantExtractor`.             |
| `CONFIG_MODE`              | `local`                                   | `local` (monolith) or `remote` (microservice).      |
| `DB_RESOLVER`              | `easytenant.connection_manager.resolve_db` | Callable that maps `tenant_id` → database alias.     |
| `MIDDLEWARE_VERIFY_TOKEN`  | `True`                                    | Whether to verify JWT signatures in the middleware. |
| `JWT_ALGORITHM`            | `HS256`                                   | JWT algorithm for verification.                     |
| `JWT_SIGNING_KEY`          | `None` (falls back to `SECRET_KEY`)       | Key for JWT verification.                           |
| `ENCRYPTION_KEY`           | `None` (derives from `SECRET_KEY`)        | Fernet key for encrypting credentials.              |
| `RELOAD_SECRET`            | `None`                                    | Secret for the `/tenants/reload/` HTTP endpoint.     |
| `CACHE_TTL`                | `300`                                     | Cache TTL in seconds (remote mode only).            |
| `SERVICE_TOKEN`            | `None`                                    | Bearer token for auth service API (remote mode).    |
| `REMOTE_TENANT_CONFIG_URL`  | `None`                                    | Base URL of auth service (remote mode).             |
| `REMOTE_TENANT_CONFIG_PATH` | `/tenant-config/`                          | Path to tenant config API (remote mode).             |
| `ADMIN_TENANT_PARAM`        | `tenant`                                   | Query parameter name for admin tenant selection.     |

---

## Composing with Schema-Level Tenancy

`django-easytenant` operates at the **database connection** layer. Schema-level libraries like `django-tenants` operate at the **schema/search_path** layer. They can be composed:

```python
# Each tenant gets their own PostgreSQL schema within a tenant database.
# django-easytenant routes to the correct database instance.
# django-tenants sets the search_path within that database.
```

---

## Examples

See [`examples/monolith/`](examples/monolith/) for a complete working example with 3 databases, a custom User model, and BlogPost model.

---

## License

MIT
