import pytest

from easyshard.connection_manager import reload
from easyshard.context import reset_shard_id, set_shard_id
from easyshard.models import ShardConfig
from easyshard.routers import ShardRouter
from tests.testapp.models import BlogPost


@pytest.mark.django_db
class TestShardRouter:
    def setup_method(self):
        self.router = ShardRouter()

    def test_shardconfig_routes_to_default(self):
        assert self.router.db_for_read(ShardConfig) == "default"
        assert self.router.db_for_write(ShardConfig) == "default"

    def test_no_context_routes_to_default(self):
        token = set_shard_id(None)
        assert self.router.db_for_read(BlogPost) == "default"
        assert self.router.db_for_write(BlogPost) == "default"
        reset_shard_id(token)

    def test_sharded_model_routes_to_shard(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="east", db_alias="shard_trial")
        reload()

        token = set_shard_id("east")
        assert self.router.db_for_read(BlogPost) == "shard_trial"
        assert self.router.db_for_write(BlogPost) == "shard_trial"
        reset_shard_id(token)

    def test_allow_relation_always_true(self):
        assert self.router.allow_relation(None, None) is True

    def test_allow_migrate_easyshard_default_only(self):
        assert self.router.allow_migrate("default", "easyshard") is True
        assert self.router.allow_migrate("shard_trial", "easyshard") is False

    def test_allow_migrate_other_apps_everywhere(self):
        assert self.router.allow_migrate("default", "testapp") is True
        assert self.router.allow_migrate("shard_trial", "testapp") is True
