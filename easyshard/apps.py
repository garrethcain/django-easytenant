from django.apps import AppConfig


class EasyShardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "easyshard"
    verbose_name = "EasyShard"

    def ready(self):
        from easyshard.signals import connect_signals

        connect_signals()
