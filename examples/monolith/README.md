# django-easytenant — Monolith Example

A minimal Django project with database-per-tenant routing using `django-easytenant`.

## What this demonstrates

- **3 databases**: `default` (auth + TenantConfig), `tenant_trial`, `tenant_enterprise`
- **Custom User** with `TenantUserMixin` for manual tenant assignment
- **BlogPost model** that automatically routes to the correct tenant database
- **TenantMiddleware** extracting `tenant_id` from JWT tokens
- **TenantRouter** directing all non-easytenant queries to the tenant DB

## Setup

```bash
cd examples/monolith

# Create virtualenv and install dependencies (including easytenant from parent)
uv sync

# Apply migrations to all three databases
uv run python manage.py migrate
uv run python manage.py migrate --database=tenant_trial
uv run python manage.py migrate --database=tenant_enterprise

# Create TenantConfig rows on the default database
uv run python manage.py shell
```

```python
from easytenant.models import TenantConfig

TenantConfig.objects.create(
    tenant_id="trial",
    db_alias="tenant_trial",
    name=str(__import__("pathlib").Path("db_trial.sqlite3").resolve()),
    host="localhost",
    port=5432,
    user="app",
    password="trial-db-password",
)

TenantConfig.objects.create(
    tenant_id="enterprise",
    db_alias="tenant_enterprise",
    name=str(__import__("pathlib").Path("db_enterprise.sqlite3").resolve()),
    host="localhost",
    port=5432,
    user="app",
    password="enterprise-db-password",
)
```

```bash
# Reload tenant configs into the connection manager
uv run python manage.py reload_tenants

# Create a superuser (on default DB)
uv run python manage.py createsuperuser

# Run the server
uv run python manage.py runserver
```

## How it works

1. A user authenticates and receives a JWT containing a `tenant_id` claim.
2. On each request, `TenantMiddleware` extracts the `tenant_id` from the JWT.
3. `TenantRouter` routes all queries (except `easytenant` app models) to the tenant database.
4. `TenantConfig` and easytenant internal tables always route to `default`.

## Admin access

The admin supports a `?tenant=` query parameter for browsing data on specific tenants:

```
/admin/blog/blogpost/?tenant=trial
/admin/blog/blogpost/?tenant=enterprise
```
