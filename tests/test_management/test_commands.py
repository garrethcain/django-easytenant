import pytest
from django.core.management import call_command
from io import StringIO

from easyshard import connection_manager


@pytest.mark.django_db
class TestReloadShardsCommand:
    def test_reload_local_mode(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="alpha", db_alias="shard_alpha")
        connection_manager._loaded = False

        out = StringIO()
        call_command("reload_shards", stdout=out)
        assert "reloaded successfully" in out.getvalue()

    def test_reload_clears_and_repopulates(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="beta", db_alias="shard_beta")
        connection_manager.reload()

        assert connection_manager.resolve_db("beta") == "shard_beta"

        make_shard_config(shard_id="gamma", db_alias="shard_gamma")

        out = StringIO()
        call_command("reload_shards", stdout=out)

        assert connection_manager.resolve_db("gamma") == "shard_gamma"
