import pytest

from easyshard.connection_manager import get_all_aliases, reload, resolve_db
from easyshard.exceptions import ShardNotConfiguredError


@pytest.mark.django_db
class TestLocalShardConnectionManager:
    def test_resolve_db(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="east", db_alias="shard_trial")
        reload()
        assert resolve_db("east") == "shard_trial"

    def test_resolve_db_not_found(self):
        reload()
        with pytest.raises(ShardNotConfiguredError) as exc:
            resolve_db("nonexistent")
        assert "nonexistent" in str(exc.value)

    def test_resolve_db_inactive(self):
        from tests.conftest import make_shard_config

        make_shard_config(
            shard_id="inactive",
            db_alias="shard_inactive",
            name="inactive",
            is_active=False,
        )
        reload()
        with pytest.raises(ShardNotConfiguredError):
            resolve_db("inactive")

    def test_reload_clears_cache(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="east", db_alias="shard_trial")
        reload()
        assert resolve_db("east") == "shard_trial"

        from easyshard.models import ShardConfig

        ShardConfig.objects.filter(shard_id="east").delete()
        reload()

        with pytest.raises(ShardNotConfiguredError):
            resolve_db("east")

    def test_get_all_aliases(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="a", db_alias="shard_trial")
        make_shard_config(shard_id="b", db_alias="shard_enterprise")
        reload()
        aliases = get_all_aliases()
        assert "shard_trial" in aliases
        assert "shard_enterprise" in aliases

    def test_injects_into_connections(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="east", db_alias="shard_trial")
        reload()

        from django.db import connections

        assert "shard_trial" in connections.settings
        assert connections.settings["shard_trial"]["ENGINE"] == "django.db.backends.sqlite3"
