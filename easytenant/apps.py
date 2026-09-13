from django.apps import AppConfig


class EasyTenantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "easytenant"
    verbose_name = "EasyTenant"

    def ready(self):
        from easytenant.signals import connect_signals

        connect_signals()
