from django.core.checks import Warning, register


@register()
def check_tenant_settings(app_configs, **kwargs):
    """System checks for django-easytenant configuration."""
    from easytenant.settings import api_settings

    errors = []

    mode = api_settings._get_raw_setting("CONFIG_MODE") or "local"

    if mode == "remote":
        if not api_settings._get_raw_setting("REMOTE_TENANT_CONFIG_URL"):
            errors.append(
                Warning(
                    "REMOTE_TENANT_CONFIG_URL is not set. Required when CONFIG_MODE='remote'.",
                    id="easytenant.W001",
                )
            )
        if not api_settings._get_raw_setting("SERVICE_TOKEN"):
            errors.append(
                Warning(
                    "SERVICE_TOKEN is not set. Required when CONFIG_MODE='remote'.",
                    id="easytenant.W002",
                )
            )

    if not api_settings._get_raw_setting("ENCRYPTION_KEY"):
        errors.append(
            Warning(
                "ENCRYPTION_KEY is not set. "
                "Falling back to SECRET_KEY-derived key. "
                "Set a dedicated key for production.",
                id="easytenant.W003",
            )
        )

    return errors
