from django.core.management.base import BaseCommand

from easyshard.settings import api_settings


class Command(BaseCommand):
    help = "Reload shard database configurations from ShardConfig table"

    def handle(self, *args, **options):
        mode = api_settings._get_raw_setting("CONFIG_MODE") or "local"

        if mode == "local":
            from easyshard.connection_manager import reload as do_reload
        else:
            from easyshard.remote_connection_manager import reload as do_reload

        try:
            do_reload()
            self.stdout.write(self.style.SUCCESS("Shard configs reloaded successfully"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to reload shard configs: {e}"))
