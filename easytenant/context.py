import contextvars
from typing import Optional

_tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "easytenant_tenant_id", default=None
)


def set_tenant_id(tenant_id: Optional[str]) -> contextvars.Token:
    """Set the tenant_id for the current async/thread context.

    Returns a token that should be passed to reset_tenant_id() when done.
    """
    return _tenant_id_var.set(tenant_id)


def get_tenant_id() -> Optional[str]:
    """Get the tenant_id for the current context, or None if not set."""
    return _tenant_id_var.get()


def reset_tenant_id(token: contextvars.Token) -> None:
    """Reset the tenant_id to its previous value using the token from set_tenant_id()."""
    _tenant_id_var.reset(token)
