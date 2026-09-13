import pytest

from easytenant.connection_manager import get_all_aliases, reload, resolve_db
from easytenant.exceptions import TenantNotConfiguredError


@pytest.mark.django_db
class TestLocalTenantConnectionManager:
    def test_resolve_db(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="east", db_alias="tenant_trial")
        reload()
        assert resolve_db("east") == "tenant_trial"

    def test_resolve_db_not_found(self):
        reload()
        with pytest.raises(TenantNotConfiguredError) as exc:
            resolve_db("nonexistent")
        assert "nonexistent" in str(exc.value)

    def test_resolve_db_inactive(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(
            tenant_id="inactive",
            db_alias="tenant_inactive",
            name="inactive",
            is_active=False,
        )
        reload()
        with pytest.raises(TenantNotConfiguredError):
            resolve_db("inactive")

    def test_reload_clears_cache(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="east", db_alias="tenant_trial")
        reload()
        assert resolve_db("east") == "tenant_trial"

        from easytenant.models import TenantConfig

        TenantConfig.objects.filter(tenant_id="east").delete()
        reload()

        with pytest.raises(TenantNotConfiguredError):
            resolve_db("east")

    def test_get_all_aliases(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="a", db_alias="tenant_trial")
        make_tenant_config(tenant_id="b", db_alias="tenant_enterprise")
        reload()
        aliases = get_all_aliases()
        assert "tenant_trial" in aliases
        assert "tenant_enterprise" in aliases

    def test_injects_into_connections(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="east", db_alias="tenant_trial")
        reload()

        from django.db import connections

        assert "tenant_trial" in connections.settings
        assert connections.settings["tenant_trial"]["ENGINE"] == "django.db.backends.sqlite3"
