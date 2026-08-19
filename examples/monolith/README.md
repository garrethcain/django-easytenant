# django-easyshard — Monolith Example

A minimal Django project with database-per-tenant sharding using `django-easyshard`.

## What this demonstrates

- **3 databases**: `default` (auth + ShardConfig), `shard_trial`, `shard_enterprise`
- **Custom User** with `ShardUserMixin` for manual shard assignment
- **BlogPost model** that automatically routes to the correct shard database
- **ShardMiddleware** extracting `shard_id` from JWT tokens
- **ShardRouter** directing all non-easyshard queries to the shard DB

## Setup

```bash
cd examples/monolith

# Create virtualenv and install dependencies (including easyshard from parent)
uv sync

# Apply migrations to all three databases
uv run python manage.py migrate
uv run python manage.py migrate --database=shard_trial
uv run python manage.py migrate --database=shard_enterprise

# Create ShardConfig rows on the default database
uv run python manage.py shell
```

```python
from easyshard.models import ShardConfig

ShardConfig.objects.create(
    shard_id="trial",
    db_alias="shard_trial",
    name=str(__import__("pathlib").Path("db_trial.sqlite3").resolve()),
    host="localhost",
    port=5432,
    user="app",
    password="trial-db-password",
)

ShardConfig.objects.create(
    shard_id="enterprise",
    db_alias="shard_enterprise",
    name=str(__import__("pathlib").Path("db_enterprise.sqlite3").resolve()),
    host="localhost",
    port=5432,
    user="app",
    password="enterprise-db-password",
)
```

```bash
# Reload shard configs into the connection manager
uv run python manage.py reload_shards

# Create a superuser (on default DB)
uv run python manage.py createsuperuser

# Run the server
uv run python manage.py runserver
```

## How it works

1. A user authenticates and receives a JWT containing a `shard_id` claim.
2. On each request, `ShardMiddleware` extracts the `shard_id` from the JWT.
3. `ShardRouter` routes all queries (except `easyshard` app models) to the shard database.
4. `ShardConfig` and easyshard internal tables always route to `default`.

## Admin access

The admin supports a `?shard=` query parameter for browsing data on specific shards:

```
/admin/blog/blogpost/?shard=trial
/admin/blog/blogpost/?shard=enterprise
```
