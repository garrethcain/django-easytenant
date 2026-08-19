import pytest

from easyshard.context import reset_shard_id, set_shard_id


@pytest.fixture
def shard_context():
    """Set a shard_id in the context for the duration of the test."""
    token = set_shard_id("trial")
    yield "trial"
    reset_shard_id(token)


@pytest.fixture
def no_shard_context():
    """Ensure no shard_id is set."""
    token = set_shard_id(None)
    yield None
    reset_shard_id(token)


@pytest.fixture(autouse=True)
def reset_connection_manager():
    """Reset the connection manager cache after each test."""
    yield
    from easyshard.connection_manager import reload

    try:
        reload()
    except Exception:
        pass


def make_shard_config(**kwargs):
    """Helper to create a ShardConfig with sqlite3 defaults for testing."""
    from easyshard.models import ShardConfig

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
    return ShardConfig.objects.create(**defaults)
