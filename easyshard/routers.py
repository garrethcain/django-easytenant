from easyshard.context import get_shard_id
from easyshard.settings import api_settings

SHARD_APP_LABEL = "easyshard"


class ShardRouter:
    """Database router that directs queries to the correct shard database.

    When a shard_id is set in the request context (via middleware),
    all queries route to that shard's database. The ShardConfig model
    and easyshard internal tables always route to 'default'.

    All other models route to the shard DB when context is active,
    or 'default' when no context is set.
    """

    def _get_resolver(self):
        return api_settings.DB_RESOLVER

    def _resolve_db(self, shard_id: str) -> str:
        resolver = self._get_resolver()
        return resolver(shard_id)

    def db_for_read(self, model, **hints):
        if model._meta.app_label == SHARD_APP_LABEL:
            return "default"

        shard_id = get_shard_id()
        if shard_id is None:
            return "default"

        return self._resolve_db(shard_id)

    def db_for_write(self, model, **hints):
        if model._meta.app_label == SHARD_APP_LABEL:
            return "default"

        shard_id = get_shard_id()
        if shard_id is None:
            return "default"

        return self._resolve_db(shard_id)

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, **hints):
        if app_label == SHARD_APP_LABEL:
            return db == "default"
        return True
