import logging

from django.db.models.signals import post_delete, post_save

from easytenant.models import TenantConfig

logger = logging.getLogger("easytenant")


def _on_tenantconfig_save(sender, instance, **kwargs):
    logger.debug("TenantConfig saved: %s — reloading connections", instance.tenant_id)
    _reload()


def _on_tenantconfig_delete(sender, instance, **kwargs):
    logger.debug("TenantConfig deleted: %s — reloading connections", instance.tenant_id)
    _reload()


def _reload():
    from easytenant.settings import api_settings

    mode = api_settings._get_raw_setting("CONFIG_MODE") or "local"

    if mode == "local":
        from easytenant.connection_manager import reload as do_reload
    else:
        from easytenant.remote_connection_manager import reload as do_reload

    try:
        do_reload()
    except Exception as e:
        logger.error("Failed to reload tenant configs: %s", e)


def connect_signals():
    """Connect signal handlers. Called from AppConfig.ready()."""
    post_save.connect(_on_tenantconfig_save, sender=TenantConfig)
    post_delete.connect(_on_tenantconfig_delete, sender=TenantConfig)
