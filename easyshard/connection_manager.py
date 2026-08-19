import logging
import threading
from typing import Dict, Optional

from django.db import connections

from easyshard.exceptions import ShardNotConfiguredError

logger = logging.getLogger("easyshard")

_cache_lock = threading.Lock()
_cache: Dict[str, str] = {}
_loaded = False


def _load():
    """Load all active ShardConfig rows and inject connections."""
    global _cache, _loaded

    from easyshard.models import ShardConfig

    configs = ShardConfig.objects.filter(is_active=True)
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
        new_cache[config.shard_id] = config.db_alias
        logger.debug("Loaded shard config: %s → %s", config.shard_id, config.db_alias)

    with _cache_lock:
        _cache = new_cache
        _loaded = True


def _ensure_loaded():
    if not _loaded:
        _load()


def resolve_db(shard_id: str) -> str:
    """Resolve a shard_id to a database alias.

    The default DB_RESOLVER used by ShardRouter.
    Raises ShardNotConfiguredError if no matching config exists.
    """
    _ensure_loaded()

    with _cache_lock:
        db_alias = _cache.get(shard_id)

    if db_alias is None:
        raise ShardNotConfiguredError(shard_id)

    return db_alias


def get_all_aliases() -> list[str]:
    """Return all known shard db aliases."""
    _ensure_loaded()
    with _cache_lock:
        return list(set(_cache.values()))


def reload():
    """Clear cache and re-read all ShardConfig rows."""
    global _loaded
    with _cache_lock:
        _cache.clear()
        _loaded = False
    _load()
    logger.info("Shard configs reloaded: %d active shards", len(_cache))
