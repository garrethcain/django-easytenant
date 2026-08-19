import logging
import threading
import time
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet
from django.db import connections

from easyshard.exceptions import ShardNotConfiguredError, ShardConnectionError

logger = logging.getLogger("easyshard")

_cache_lock = threading.Lock()
_cache: Dict[str, Tuple[str, float]] = {}
_ttl: int = 300


def _get_ttl() -> int:
    from easyshard.settings import api_settings

    return api_settings.CACHE_TTL


def _get_service_token() -> str:
    from easyshard.settings import api_settings

    token = api_settings._get_raw_setting("SERVICE_TOKEN")
    if not token:
        raise ShardConnectionError("SERVICE_TOKEN is required for remote mode")
    return token


def _get_remote_url() -> str:
    from easyshard.settings import api_settings

    base_url = api_settings._get_raw_setting("REMOTE_SHARD_CONFIG_URL")
    if not base_url:
        raise ShardConnectionError("REMOTE_SHARD_CONFIG_URL is required for remote mode")

    path = api_settings.REMOTE_SHARD_CONFIG_PATH
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _get_fernet() -> Fernet:
    from easyshard.settings import api_settings

    return Fernet(api_settings.encryption_key)


def _fetch_config(shard_id: str) -> dict:
    """Fetch a single shard config from the auth service."""
    try:
        import requests
    except ImportError:
        raise ImportError(
            "requests is required for remote mode. Install with: pip install django-easyshard[remote]"
        )

    url = f"{_get_remote_url()}{shard_id}/"
    headers = {"Authorization": f"Bearer {_get_service_token()}"}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ShardConnectionError(f"Failed to fetch shard config for '{shard_id}' from auth service: {e}")

    data = response.json()

    fernet = _get_fernet()
    try:
        password = fernet.decrypt(data["password"].encode()).decode()
    except Exception as e:
        raise ShardConnectionError(f"Failed to decrypt shard password: {e}")

    return {
        "ENGINE": data["engine"],
        "NAME": data["name"],
        "HOST": data["host"],
        "PORT": data["port"],
        "USER": data["user"],
        "PASSWORD": password,
    }


def resolve_db(shard_id: str) -> str:
    """Resolve a shard_id to a database alias, fetching from auth service if needed."""
    ttl = _get_ttl()
    now = time.time()

    with _cache_lock:
        cached = _cache.get(shard_id)
        if cached is not None:
            db_alias, expires_at = cached
            if now < expires_at:
                return db_alias

    data = _fetch_config(shard_id)
    db_alias = data.pop("db_alias", None) or f"shard_{shard_id}"

    data.setdefault("ATOMIC_REQUESTS", False)
    data.setdefault("AUTOCOMMIT", True)
    data.setdefault("CONN_MAX_AGE", 0)
    data.setdefault("CONN_HEALTH_CHECKS", False)
    data.setdefault("OPTIONS", {})
    data.setdefault("TIME_ZONE", None)
    data.setdefault("TEST", {})
    connections.settings[db_alias] = data

    with _cache_lock:
        _cache[shard_id] = (db_alias, now + ttl)

    logger.debug("Fetched shard config: %s → %s", shard_id, db_alias)
    return db_alias


def get_all_aliases() -> list[str]:
    """Return all cached shard db aliases."""
    with _cache_lock:
        return [alias for alias, _ in _cache.values()]


def reload():
    """Clear cache, forcing re-fetch on next request."""
    with _cache_lock:
        _cache.clear()
    logger.info("Remote shard config cache cleared")
