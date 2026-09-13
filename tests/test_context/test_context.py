import pytest

from easytenant.context import get_tenant_id, reset_tenant_id, set_tenant_id


class TestContextVar:
    def test_default_is_none(self):
        assert get_tenant_id() is None

    def test_set_and_get(self):
        token = set_tenant_id("east")
        assert get_tenant_id() == "east"
        reset_tenant_id(token)

    def test_reset_restores_previous(self):
        token1 = set_tenant_id("east")
        token2 = set_tenant_id("west")

        assert get_tenant_id() == "west"
        reset_tenant_id(token2)
        assert get_tenant_id() == "east"
        reset_tenant_id(token1)

    def test_set_none(self):
        token = set_tenant_id(None)
        assert get_tenant_id() is None
        reset_tenant_id(token)

    def test_isolation_between_contexts(self):
        import contextvars

        ctx = contextvars.copy_context()

        results = {}

        def in_context(tenant, key):
            set_tenant_id(tenant)
            results[key] = get_tenant_id()

        ctx.run(in_context, "east", "ctx1")

        assert results["ctx1"] == "east"
        assert get_tenant_id() is None
