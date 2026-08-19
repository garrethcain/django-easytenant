import logging

from django.db.models.signals import post_delete, post_save

from easyshard.models import ShardConfig

logger = logging.getLogger("easyshard")


def _on_shardconfig_save(sender, instance, **kwargs):
    logger.debug("ShardConfig saved: %s — reloading connections", instance.shard_id)
    _reload()


def _on_shardconfig_delete(sender, instance, **kwargs):
    logger.debug("ShardConfig deleted: %s — reloading connections", instance.shard_id)
    _reload()


def _reload():
    from easyshard.settings import api_settings

    mode = api_settings._get_raw_setting("CONFIG_MODE") or "local"

    if mode == "local":
        from easyshard.connection_manager import reload as do_reload
    else:
        from easyshard.remote_connection_manager import reload as do_reload

    try:
        do_reload()
    except Exception as e:
        logger.error("Failed to reload shard configs: %s", e)


def connect_signals():
    """Connect signal handlers. Called from AppConfig.ready()."""
    post_save.connect(_on_shardconfig_save, sender=ShardConfig)
    post_delete.connect(_on_shardconfig_delete, sender=ShardConfig)
