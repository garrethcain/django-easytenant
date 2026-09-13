class EasyTenantError(Exception):
    """Base exception for django-easytenant."""


class TenantNotConfiguredError(EasyTenantError):
    """Raised when a tenant_id has no matching active TenantConfig."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(
            f"No active TenantConfig found for tenant_id='{tenant_id}'. "
            f"Create a TenantConfig record or check is_active flag."
        )


class TenantConnectionError(EasyTenantError):
    """Raised when a tenant database connection cannot be established."""


class TenantExtractionError(EasyTenantError):
    """Raised when tenant_id extraction from a request fails."""
