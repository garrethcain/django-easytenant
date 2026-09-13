import json

import pytest
from django.test import Client


@pytest.mark.django_db
class TestTenantConfigDetailView:
    def setup_method(self):
        self.client = Client()

    def test_unauthorized(self, settings):
        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "SERVICE_TOKEN": "secret"}
        from easytenant.settings import api_settings

        api_settings.reload()
        response = self.client.get("/tenant-config/east/")
        assert response.status_code == 401

    def test_not_found(self, settings):
        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "SERVICE_TOKEN": "secret"}
        from easytenant.settings import api_settings

        api_settings.reload()
        response = self.client.get(
            "/tenant-config/nonexistent/",
            HTTP_AUTHORIZATION="Bearer secret",
        )
        assert response.status_code == 404

    def test_returns_config(self, settings):
        from tests.conftest import make_tenant_config

        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "SERVICE_TOKEN": "secret"}
        from easytenant.settings import api_settings

        api_settings.reload()

        make_tenant_config(
            tenant_id="east",
            db_alias="tenant_trial",
            name="trial",
            host="localhost",
            password="mypassword",
        )

        response = self.client.get(
            "/tenant-config/east/",
            HTTP_AUTHORIZATION="Bearer secret",
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["tenant_id"] == "east"
        assert data["db_alias"] == "tenant_trial"
        assert data["password"] != "mypassword"


@pytest.mark.django_db
class TestReloadTenantsView:
    def setup_method(self):
        self.client = Client()

    def test_unauthorized(self, settings):
        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "RELOAD_SECRET": "reload-secret"}
        from easytenant.settings import api_settings

        api_settings.reload()
        response = self.client.post("/tenants/reload/")
        assert response.status_code == 403

    def test_reload_success(self, settings):
        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "RELOAD_SECRET": "reload-secret"}
        from easytenant.settings import api_settings

        api_settings.reload()

        response = self.client.post(
            "/tenants/reload/",
            HTTP_X_TENANT_RELOAD_SECRET="reload-secret",
        )
        assert response.status_code == 200
