import jwt
import pytest
from django.test import RequestFactory

from easytenant.connection_manager import reload
from easytenant.context import get_tenant_id
from easytenant.middleware import TenantMiddleware


def dummy_get_response(request):
    from django.http import HttpResponse

    return HttpResponse("ok")


@pytest.mark.django_db
class TestTenantMiddleware:
    def setup_method(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(dummy_get_response)

    def test_jwt_extraction_sets_context(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="east", db_alias="tenant_trial")
        reload()

        token = jwt.encode(
            {"tenant_id": "east"},
            "test-secret-key-for-easytenant-not-for-production",
            algorithm="HS256",
        )
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        captured = {}
        original_get_response = self.middleware.get_response

        def capturing_get_response(req):
            captured["tenant_id"] = get_tenant_id()
            return original_get_response(req)

        self.middleware.get_response = capturing_get_response
        self.middleware(request)
        self.middleware.get_response = original_get_response

        assert captured["tenant_id"] == "east"

    def test_context_reset_after_request(self):
        token = jwt.encode(
            {"tenant_id": "east"},
            "test-secret-key-for-easytenant-not-for-production",
            algorithm="HS256",
        )
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.middleware(request)

        assert get_tenant_id() is None

    def test_no_token_no_context(self):
        request = self.factory.get("/")
        self.middleware(request)
        assert get_tenant_id() is None

    def test_admin_query_param_fallback(self):
        request = self.factory.get("/admin/?tenant=east")

        captured = {}
        original_get_response = self.middleware.get_response

        def capturing_get_response(req):
            captured["tenant_id"] = get_tenant_id()
            return original_get_response(req)

        self.middleware.get_response = capturing_get_response
        self.middleware(request)
        self.middleware.get_response = original_get_response

        assert captured["tenant_id"] == "east"
