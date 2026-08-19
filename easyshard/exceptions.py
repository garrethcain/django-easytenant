class EasyShardError(Exception):
    """Base exception for django-easyshard."""


class ShardNotConfiguredError(EasyShardError):
    """Raised when a shard_id has no matching active ShardConfig."""

    def __init__(self, shard_id: str):
        self.shard_id = shard_id
        super().__init__(
            f"No active ShardConfig found for shard_id='{shard_id}'. "
            f"Create a ShardConfig record or check is_active flag."
        )


class ShardConnectionError(EasyShardError):
    """Raised when a shard database connection cannot be established."""


class ShardExtractionError(EasyShardError):
    """Raised when shard_id extraction from a request fails."""
