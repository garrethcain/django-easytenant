import pytest

from easytenant.connection_manager import reload
from easytenant.context import reset_tenant_id, set_tenant_id
from easytenant.models import TenantConfig
from easytenant.routers import TenantRouter
from tests.testapp.models import BlogPost


@pytest.mark.django_db
class TestTenantRouter:
    def setup_method(self):
        self.router = TenantRouter()

    def test_tenantconfig_routes_to_default(self):
        assert self.router.db_for_read(TenantConfig) == "default"
        assert self.router.db_for_write(TenantConfig) == "default"

    def test_no_context_routes_to_default(self):
        token = set_tenant_id(None)
        assert self.router.db_for_read(BlogPost) == "default"
        assert self.router.db_for_write(BlogPost) == "default"
        reset_tenant_id(token)

    def test_tenant_model_routes_to_tenant(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="east", db_alias="tenant_trial")
        reload()

        token = set_tenant_id("east")
        assert self.router.db_for_read(BlogPost) == "tenant_trial"
        assert self.router.db_for_write(BlogPost) == "tenant_trial"
        reset_tenant_id(token)

    def test_allow_relation_always_true(self):
        assert self.router.allow_relation(None, None) is True

    def test_allow_migrate_easytenant_default_only(self):
        assert self.router.allow_migrate("default", "easytenant") is True
        assert self.router.allow_migrate("tenant_trial", "easytenant") is False

    def test_allow_migrate_other_apps_everywhere(self):
        assert self.router.allow_migrate("default", "testapp") is True
        assert self.router.allow_migrate("tenant_trial", "testapp") is True
