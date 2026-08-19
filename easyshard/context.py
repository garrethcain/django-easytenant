import contextvars
from typing import Optional

_shard_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "easyshard_shard_id", default=None
)


def set_shard_id(shard_id: Optional[str]) -> contextvars.Token:
    """Set the shard_id for the current async/thread context.

    Returns a token that should be passed to reset_shard_id() when done.
    """
    return _shard_id_var.set(shard_id)


def get_shard_id() -> Optional[str]:
    """Get the shard_id for the current context, or None if not set."""
    return _shard_id_var.get()


def reset_shard_id(token: contextvars.Token) -> None:
    """Reset the shard_id to its previous value using the token from set_shard_id()."""
    _shard_id_var.reset(token)
