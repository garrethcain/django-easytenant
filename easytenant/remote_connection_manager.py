import logging
import threading
import time
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet
from django.db import connections

from easytenant.exceptions import TenantNotConfiguredError, TenantConnectionError

logger = logging.getLogger("easytenant")

_cache_lock = threading.Lock()
_cache: Dict[str, Tuple[str, float]] = {}
_ttl: int = 300


def _get_ttl() -> int:
    from easytenant.settings import api_settings

    return api_settings.CACHE_TTL


def _get_service_token() -> str:
    from easytenant.settings import api_settings

    token = api_settings._get_raw_setting("SERVICE_TOKEN")
    if not token:
        raise TenantConnectionError("SERVICE_TOKEN is required for remote mode")
    return token


def _get_remote_url() -> str:
    from easytenant.settings import api_settings

    base_url = api_settings._get_raw_setting("REMOTE_TENANT_CONFIG_URL")
    if not base_url:
        raise TenantConnectionError("REMOTE_TENANT_CONFIG_URL is required for remote mode")

    path = api_settings.REMOTE_TENANT_CONFIG_PATH
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _get_fernet() -> Fernet:
    from easytenant.settings import api_settings

    return Fernet(api_settings.encryption_key)


def _fetch_config(tenant_id: str) -> dict:
    """Fetch a single tenant config from the auth service."""
    try:
        import requests
    except ImportError:
        raise ImportError(
            "requests is required for remote mode. Install with: pip install django-easytenant[remote]"
        )

    url = f"{_get_remote_url()}{tenant_id}/"
    headers = {"Authorization": f"Bearer {_get_service_token()}"}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise TenantConnectionError(f"Failed to fetch tenant config for '{tenant_id}' from auth service: {e}")

    data = response.json()

    fernet = _get_fernet()
    try:
        password = fernet.decrypt(data["password"].encode()).decode()
    except Exception as e:
        raise TenantConnectionError(f"Failed to decrypt tenant password: {e}")

    return {
        "ENGINE": data["engine"],
        "NAME": data["name"],
        "HOST": data["host"],
        "PORT": data["port"],
        "USER": data["user"],
        "PASSWORD": password,
    }


def resolve_db(tenant_id: str) -> str:
    """Resolve a tenant_id to a database alias, fetching from auth service if needed."""
    ttl = _get_ttl()
    now = time.time()

    with _cache_lock:
        cached = _cache.get(tenant_id)
        if cached is not None:
            db_alias, expires_at = cached
            if now < expires_at:
                return db_alias

    data = _fetch_config(tenant_id)
    db_alias = data.pop("db_alias", None) or f"tenant_{tenant_id}"

    data.setdefault("ATOMIC_REQUESTS", False)
    data.setdefault("AUTOCOMMIT", True)
    data.setdefault("CONN_MAX_AGE", 0)
    data.setdefault("CONN_HEALTH_CHECKS", False)
    data.setdefault("OPTIONS", {})
    data.setdefault("TIME_ZONE", None)
    data.setdefault("TEST", {})
    connections.settings[db_alias] = data

    with _cache_lock:
        _cache[tenant_id] = (db_alias, now + ttl)

    logger.debug("Fetched tenant config: %s → %s", tenant_id, db_alias)
    return db_alias


def get_all_aliases() -> list[str]:
    """Return all cached tenant db aliases."""
    with _cache_lock:
        return [alias for alias, _ in _cache.values()]


def reload():
    """Clear cache, forcing re-fetch on next request."""
    with _cache_lock:
        _cache.clear()
    logger.info("Remote tenant config cache cleared")
