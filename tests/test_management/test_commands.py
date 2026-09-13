import pytest
from django.core.management import call_command
from io import StringIO

from easytenant import connection_manager


@pytest.mark.django_db
class TestReloadTenantsCommand:
    def test_reload_local_mode(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="alpha", db_alias="tenant_alpha")
        connection_manager._loaded = False

        out = StringIO()
        call_command("reload_tenants", stdout=out)
        assert "reloaded successfully" in out.getvalue()

    def test_reload_clears_and_repopulates(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="beta", db_alias="tenant_beta")
        connection_manager.reload()

        assert connection_manager.resolve_db("beta") == "tenant_beta"

        make_tenant_config(tenant_id="gamma", db_alias="tenant_gamma")

        out = StringIO()
        call_command("reload_tenants", stdout=out)

        assert connection_manager.resolve_db("gamma") == "tenant_gamma"
