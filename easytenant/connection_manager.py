import logging
import threading
from typing import Dict, Optional

from django.db import connections

from easytenant.exceptions import TenantNotConfiguredError

logger = logging.getLogger("easytenant")

_cache_lock = threading.Lock()
_cache: Dict[str, str] = {}
_loaded = False


def _load():
    """Load all active TenantConfig rows and inject connections."""
    global _cache, _loaded

    from easytenant.models import TenantConfig

    configs = TenantConfig.objects.filter(is_active=True)
    new_cache: Dict[str, str] = {}

    for config in configs:
        conn_dict = config.to_connection_dict()
        conn_dict.setdefault("ATOMIC_REQUESTS", False)
        conn_dict.setdefault("AUTOCOMMIT", True)
        conn_dict.setdefault("CONN_MAX_AGE", 0)
        conn_dict.setdefault("CONN_HEALTH_CHECKS", False)
        conn_dict.setdefault("OPTIONS", {})
        conn_dict.setdefault("TIME_ZONE", None)
        conn_dict.setdefault("TEST", {})
        connections.settings[config.db_alias] = conn_dict
        new_cache[config.tenant_id] = config.db_alias
        logger.debug("Loaded tenant config: %s → %s", config.tenant_id, config.db_alias)

    with _cache_lock:
        _cache = new_cache
        _loaded = True


def _ensure_loaded():
    if not _loaded:
        _load()


def resolve_db(tenant_id: str) -> str:
    """Resolve a tenant_id to a database alias.

    The default DB_RESOLVER used by TenantRouter.
    Raises TenantNotConfiguredError if no matching config exists.
    """
    _ensure_loaded()

    with _cache_lock:
        db_alias = _cache.get(tenant_id)

    if db_alias is None:
        raise TenantNotConfiguredError(tenant_id)

    return db_alias


def get_all_aliases() -> list[str]:
    """Return all known tenant db aliases."""
    _ensure_loaded()
    with _cache_lock:
        return list(set(_cache.values()))


def reload():
    """Clear cache and re-read all TenantConfig rows."""
    global _loaded
    with _cache_lock:
        _cache.clear()
        _loaded = False
    _load()
    logger.info("Tenant configs reloaded: %d active tenants", len(_cache))
