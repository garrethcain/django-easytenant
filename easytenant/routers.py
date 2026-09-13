from easytenant.context import get_tenant_id
from easytenant.settings import api_settings

TENANT_APP_LABEL = "easytenant"


class TenantRouter:
    """Database router that directs queries to the correct tenant database.

    When a tenant_id is set in the request context (via middleware),
    all queries route to that tenant's database. The TenantConfig model
    and easytenant internal tables always route to 'default'.

    All other models route to the tenant DB when context is active,
    or 'default' when no context is set.
    """

    def _get_resolver(self):
        return api_settings.DB_RESOLVER

    def _resolve_db(self, tenant_id: str) -> str:
        resolver = self._get_resolver()
        return resolver(tenant_id)

    def db_for_read(self, model, **hints):
        if model._meta.app_label == TENANT_APP_LABEL:
            return "default"

        tenant_id = get_tenant_id()
        if tenant_id is None:
            return "default"

        return self._resolve_db(tenant_id)

    def db_for_write(self, model, **hints):
        if model._meta.app_label == TENANT_APP_LABEL:
            return "default"

        tenant_id = get_tenant_id()
        if tenant_id is None:
            return "default"

        return self._resolve_db(tenant_id)

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, **hints):
        if app_label == TENANT_APP_LABEL:
            return db == "default"
        return True
