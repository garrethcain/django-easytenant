import pytest

from easyshard.context import get_shard_id, reset_shard_id, set_shard_id


class TestContextVar:
    def test_default_is_none(self):
        assert get_shard_id() is None

    def test_set_and_get(self):
        token = set_shard_id("east")
        assert get_shard_id() == "east"
        reset_shard_id(token)

    def test_reset_restores_previous(self):
        token1 = set_shard_id("east")
        token2 = set_shard_id("west")

        assert get_shard_id() == "west"
        reset_shard_id(token2)
        assert get_shard_id() == "east"
        reset_shard_id(token1)

    def test_set_none(self):
        token = set_shard_id(None)
        assert get_shard_id() is None
        reset_shard_id(token)

    def test_isolation_between_contexts(self):
        import contextvars

        ctx = contextvars.copy_context()

        results = {}

        def in_context(shard, key):
            set_shard_id(shard)
            results[key] = get_shard_id()

        ctx.run(in_context, "east", "ctx1")

        assert results["ctx1"] == "east"
        assert get_shard_id() is None
