import json

import pytest
from django.test import Client


@pytest.mark.django_db
class TestShardConfigDetailView:
    def setup_method(self):
        self.client = Client()

    def test_unauthorized(self, settings):
        settings.EASY_SHARD = {**getattr(settings, "EASY_SHARD", {}), "SERVICE_TOKEN": "secret"}
        from easyshard.settings import api_settings

        api_settings.reload()
        response = self.client.get("/shard-config/east/")
        assert response.status_code == 401

    def test_not_found(self, settings):
        settings.EASY_SHARD = {**getattr(settings, "EASY_SHARD", {}), "SERVICE_TOKEN": "secret"}
        from easyshard.settings import api_settings

        api_settings.reload()
        response = self.client.get(
            "/shard-config/nonexistent/",
            HTTP_AUTHORIZATION="Bearer secret",
        )
        assert response.status_code == 404

    def test_returns_config(self, settings):
        from tests.conftest import make_shard_config

        settings.EASY_SHARD = {**getattr(settings, "EASY_SHARD", {}), "SERVICE_TOKEN": "secret"}
        from easyshard.settings import api_settings

        api_settings.reload()

        make_shard_config(
            shard_id="east",
            db_alias="shard_trial",
            name="trial",
            host="localhost",
            password="mypassword",
        )

        response = self.client.get(
            "/shard-config/east/",
            HTTP_AUTHORIZATION="Bearer secret",
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["shard_id"] == "east"
        assert data["db_alias"] == "shard_trial"
        assert data["password"] != "mypassword"


@pytest.mark.django_db
class TestReloadShardsView:
    def setup_method(self):
        self.client = Client()

    def test_unauthorized(self, settings):
        settings.EASY_SHARD = {**getattr(settings, "EASY_SHARD", {}), "RELOAD_SECRET": "reload-secret"}
        from easyshard.settings import api_settings

        api_settings.reload()
        response = self.client.post("/shards/reload/")
        assert response.status_code == 403

    def test_reload_success(self, settings):
        settings.EASY_SHARD = {**getattr(settings, "EASY_SHARD", {}), "RELOAD_SECRET": "reload-secret"}
        from easyshard.settings import api_settings

        api_settings.reload()

        response = self.client.post(
            "/shards/reload/",
            HTTP_X_SHARD_RELOAD_SECRET="reload-secret",
        )
        assert response.status_code == 200
