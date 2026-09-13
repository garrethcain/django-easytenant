import pytest

from easytenant.context import reset_tenant_id, set_tenant_id


@pytest.fixture
def tenant_context():
    """Set a tenant_id in the context for the duration of the test."""
    token = set_tenant_id("trial")
    yield "trial"
    reset_tenant_id(token)


@pytest.fixture
def no_tenant_context():
    """Ensure no tenant_id is set."""
    token = set_tenant_id(None)
    yield None
    reset_tenant_id(token)


@pytest.fixture(autouse=True)
def reset_connection_manager():
    """Reset the connection manager cache after each test."""
    yield
    from easytenant.connection_manager import reload

    try:
        reload()
    except Exception:
        pass


def make_tenant_config(**kwargs):
    """Helper to create a TenantConfig with sqlite3 defaults for testing."""
    from easytenant.models import TenantConfig

    defaults = {
        "engine": "django.db.backends.sqlite3",
        "name": ":memory:",
        "host": "localhost",
        "port": 5432,
        "user": "app",
        "password": "secret",
        "is_active": True,
    }
    defaults.update(kwargs)
    return TenantConfig.objects.create(**defaults)
