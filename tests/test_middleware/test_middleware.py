import jwt
import pytest
from django.test import RequestFactory

from easyshard.connection_manager import reload
from easyshard.context import get_shard_id
from easyshard.middleware import ShardMiddleware


def dummy_get_response(request):
    from django.http import HttpResponse

    return HttpResponse("ok")


@pytest.mark.django_db
class TestShardMiddleware:
    def setup_method(self):
        self.factory = RequestFactory()
        self.middleware = ShardMiddleware(dummy_get_response)

    def test_jwt_extraction_sets_context(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="east", db_alias="shard_trial")
        reload()

        token = jwt.encode(
            {"shard_id": "east"},
            "test-secret-key-for-easyshard-not-for-production",
            algorithm="HS256",
        )
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        captured = {}
        original_get_response = self.middleware.get_response

        def capturing_get_response(req):
            captured["shard_id"] = get_shard_id()
            return original_get_response(req)

        self.middleware.get_response = capturing_get_response
        self.middleware(request)
        self.middleware.get_response = original_get_response

        assert captured["shard_id"] == "east"

    def test_context_reset_after_request(self):
        token = jwt.encode(
            {"shard_id": "east"},
            "test-secret-key-for-easyshard-not-for-production",
            algorithm="HS256",
        )
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.middleware(request)

        assert get_shard_id() is None

    def test_no_token_no_context(self):
        request = self.factory.get("/")
        self.middleware(request)
        assert get_shard_id() is None

    def test_admin_query_param_fallback(self):
        request = self.factory.get("/admin/?shard=east")

        captured = {}
        original_get_response = self.middleware.get_response

        def capturing_get_response(req):
            captured["shard_id"] = get_shard_id()
            return original_get_response(req)

        self.middleware.get_response = capturing_get_response
        self.middleware(request)
        self.middleware.get_response = original_get_response

        assert captured["shard_id"] == "east"
