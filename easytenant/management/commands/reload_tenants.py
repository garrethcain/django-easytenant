from django.core.management.base import BaseCommand

from easytenant.settings import api_settings


class Command(BaseCommand):
    help = "Reload tenant database configurations from TenantConfig table"

    def handle(self, *args, **options):
        mode = api_settings._get_raw_setting("CONFIG_MODE") or "local"

        if mode == "local":
            from easytenant.connection_manager import reload as do_reload
        else:
            from easytenant.remote_connection_manager import reload as do_reload

        try:
            do_reload()
            self.stdout.write(self.style.SUCCESS("Tenant configs reloaded successfully"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to reload tenant configs: {e}"))
