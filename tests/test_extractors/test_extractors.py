import jwt
import pytest
from django.test import RequestFactory

from easytenant.extractors import (
    AdminTenantExtractor,
    HeaderTenantExtractor,
    JWTTenantExtractor,
    SessionTenantExtractor,
)
from easytenant.settings import api_settings


class TestJWTTenantExtractor:
    def setup_method(self):
        self.factory = RequestFactory()
        self.extractor = JWTTenantExtractor()

    def _make_token(self, payload, key="test-secret-key-for-easytenant-not-for-production"):
        return jwt.encode(payload, key, algorithm="HS256")

    def test_extract_with_tenant_id(self):
        token = self._make_token({"tenant_id": "east"})
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
        assert self.extractor(request) == "east"

    def test_extract_without_tenant_id_claim(self):
        token = self._make_token({"user_id": 1})
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
        assert self.extractor(request) is None

    def test_extract_no_auth_header(self):
        request = self.factory.get("/")
        assert self.extractor(request) is None

    def test_extract_malformed_header(self):
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer")
        assert self.extractor(request) is None

    def test_extract_invalid_token(self):
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer invalid.token.here")
        assert self.extractor(request) is None

    def test_extract_no_verify(self, settings):
        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "MIDDLEWARE_VERIFY_TOKEN": False}
        api_settings.reload()
        try:
            token = self._make_token({"tenant_id": "east"}, key="wrong-key")
            request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
            assert self.extractor(request) == "east"
        finally:
            settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "MIDDLEWARE_VERIFY_TOKEN": True}
            api_settings.reload()

    def test_custom_claim_name(self, settings):
        settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "ID_JWT_CLAIM": "tenant"}
        api_settings.reload()
        try:
            token = self._make_token({"tenant": "west"})
            request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
            assert self.extractor(request) == "west"
        finally:
            settings.EASY_TENANT = {**getattr(settings, "EASY_TENANT", {}), "ID_JWT_CLAIM": "tenant_id"}
            api_settings.reload()


class TestHeaderTenantExtractor:
    def setup_method(self):
        self.factory = RequestFactory()
        self.extractor = HeaderTenantExtractor()

    def test_extract_present(self):
        request = self.factory.get("/", HTTP_X_TENANT_ID="east")
        assert self.extractor(request) == "east"

    def test_extract_absent(self):
        request = self.factory.get("/")
        assert self.extractor(request) is None


class TestSessionTenantExtractor:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_extract_from_session(self):
        extractor = SessionTenantExtractor()
        request = self.factory.get("/")
        request.session = {"tenant_id": "east"}
        assert extractor(request) == "east"

    def test_extract_missing(self):
        extractor = SessionTenantExtractor()
        request = self.factory.get("/")
        request.session = {}
        assert extractor(request) is None


class TestAdminTenantExtractor:
    def setup_method(self):
        self.factory = RequestFactory()
        self.extractor = AdminTenantExtractor()

    def test_extract_from_query_param(self):
        request = self.factory.get("/admin/?tenant=east")
        assert self.extractor(request) == "east"

    def test_extract_no_param(self):
        request = self.factory.get("/admin/")
        assert self.extractor(request) is None
