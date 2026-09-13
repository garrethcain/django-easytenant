import logging

from easytenant.context import reset_tenant_id, set_tenant_id
from easytenant.extractors import AdminTenantExtractor, BaseTenantExtractor
from easytenant.settings import api_settings

logger = logging.getLogger("easytenant")


class TenantMiddleware:
    """Extracts tenant_id from each request and sets it in the ContextVar.

    The extraction is delegated to the configured ID_EXTRACTOR (default: JWTTenantExtractor).
    As a fallback for admin access, the ?tenant= query param is checked.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._extractor: BaseTenantExtractor = api_settings.ID_EXTRACTOR()
        self._admin_extractor = AdminTenantExtractor()

    def __call__(self, request):
        tenant_id = self._extractor(request)

        if tenant_id is None:
            tenant_id = self._admin_extractor(request)

        token = set_tenant_id(tenant_id)

        try:
            response = self.get_response(request)
        finally:
            reset_tenant_id(token)

        return response
