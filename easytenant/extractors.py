from __future__ import annotations

import logging
from typing import Optional

from django.http import HttpRequest
from django.conf import settings

from easytenant.context import get_tenant_id
from easytenant.exceptions import TenantExtractionError

logger = logging.getLogger("easytenant")


class BaseTenantExtractor:
    """Base class for tenant ID extractors."""

    def extract(self, request: HttpRequest) -> Optional[str]:
        raise NotImplementedError

    def __call__(self, request: HttpRequest) -> Optional[str]:
        return self.extract(request)


class JWTTenantExtractor(BaseTenantExtractor):
    """Extracts tenant_id from a JWT in the Authorization header.

    Subclass and override get_signing_key() / get_algorithm() to adapt
    to any JWT system (django-easyjwt, simplejwt, custom).
    """

    def get_signing_key(self) -> str:
        """Return the key used to verify JWT signatures.

        Override this to read from your JWT library's settings.
        """
        from easytenant.settings import api_settings

        key = api_settings._get_raw_setting("JWT_SIGNING_KEY")
        if key is not None:
            return key
        return settings.SECRET_KEY

    def get_algorithm(self) -> str:
        """Return the JWT algorithm for verification."""
        from easytenant.settings import api_settings

        return api_settings._get_raw_setting("JWT_ALGORITHM") or "HS256"

    def get_jwt_claim(self) -> str:
        from easytenant.settings import api_settings

        return api_settings.ID_JWT_CLAIM

    def should_verify(self) -> bool:
        from easytenant.settings import api_settings

        return api_settings.MIDDLEWARE_VERIFY_TOKEN

    def extract(self, request: HttpRequest) -> Optional[str]:
        header = request.headers.get("Authorization", "")
        if not header:
            return None

        parts = header.split(" ", 1)
        if len(parts) != 2:
            return None

        token = parts[1].strip()
        if not token:
            return None

        try:
            import jwt
        except ImportError:
            raise ImportError(
                "PyJWT is required for JWTTenantExtractor. Install with: pip install django-easytenant[jwt]"
            )

        claim = self.get_jwt_claim()

        try:
            if self.should_verify():
                payload = jwt.decode(
                    token,
                    self.get_signing_key(),
                    algorithms=[self.get_algorithm()],
                )
            else:
                payload = jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.debug("JWT decode failed in tenant extractor: %s", e)
            return None

        tenant_id = payload.get(claim)
        if tenant_id is not None:
            return str(tenant_id)
        return None


class HeaderTenantExtractor(BaseTenantExtractor):
    """Extracts tenant_id from a configurable HTTP header."""

    def extract(self, request: HttpRequest) -> Optional[str]:
        from easytenant.settings import api_settings

        header_name = api_settings.ID_HEADER_NAME
        tenant_id = request.headers.get(header_name)
        if tenant_id is not None:
            return str(tenant_id)
        return None


class SessionTenantExtractor(BaseTenantExtractor):
    """Extracts tenant_id from the request session."""

    def extract(self, request: HttpRequest) -> Optional[str]:
        from easytenant.settings import api_settings

        claim = api_settings.ID_JWT_CLAIM
        tenant_id = request.session.get(claim)
        if tenant_id is not None:
            return str(tenant_id)
        return None


class AdminTenantExtractor(BaseTenantExtractor):
    """Extracts tenant_id from a query parameter for admin use.

    Falls back to ?tenant=east on the URL. Only intended for staff access.
    """

    def extract(self, request: HttpRequest) -> Optional[str]:
        from easytenant.settings import api_settings

        param = api_settings.ADMIN_TENANT_PARAM
        tenant_id = request.GET.get(param)
        if tenant_id is not None:
            return str(tenant_id)
        return None
