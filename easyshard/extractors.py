from __future__ import annotations

import logging
from typing import Optional

from django.http import HttpRequest
from django.conf import settings

from easyshard.context import get_shard_id
from easyshard.exceptions import ShardExtractionError

logger = logging.getLogger("easyshard")


class BaseShardExtractor:
    """Base class for shard ID extractors."""

    def extract(self, request: HttpRequest) -> Optional[str]:
        raise NotImplementedError

    def __call__(self, request: HttpRequest) -> Optional[str]:
        return self.extract(request)


class JWTShardExtractor(BaseShardExtractor):
    """Extracts shard_id from a JWT in the Authorization header.

    Subclass and override get_signing_key() / get_algorithm() to adapt
    to any JWT system (django-easyjwt, simplejwt, custom).
    """

    def get_signing_key(self) -> str:
        """Return the key used to verify JWT signatures.

        Override this to read from your JWT library's settings.
        """
        from easyshard.settings import api_settings

        key = api_settings._get_raw_setting("JWT_SIGNING_KEY")
        if key is not None:
            return key
        return settings.SECRET_KEY

    def get_algorithm(self) -> str:
        """Return the JWT algorithm for verification."""
        from easyshard.settings import api_settings

        return api_settings._get_raw_setting("JWT_ALGORITHM") or "HS256"

    def get_jwt_claim(self) -> str:
        from easyshard.settings import api_settings

        return api_settings.ID_JWT_CLAIM

    def should_verify(self) -> bool:
        from easyshard.settings import api_settings

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
                "PyJWT is required for JWTShardExtractor. Install with: pip install django-easyshard[jwt]"
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
            logger.debug("JWT decode failed in shard extractor: %s", e)
            return None

        shard_id = payload.get(claim)
        if shard_id is not None:
            return str(shard_id)
        return None


class HeaderShardExtractor(BaseShardExtractor):
    """Extracts shard_id from a configurable HTTP header."""

    def extract(self, request: HttpRequest) -> Optional[str]:
        from easyshard.settings import api_settings

        header_name = api_settings.ID_HEADER_NAME
        shard_id = request.headers.get(header_name)
        if shard_id is not None:
            return str(shard_id)
        return None


class SessionShardExtractor(BaseShardExtractor):
    """Extracts shard_id from the request session."""

    def extract(self, request: HttpRequest) -> Optional[str]:
        from easyshard.settings import api_settings

        claim = api_settings.ID_JWT_CLAIM
        shard_id = request.session.get(claim)
        if shard_id is not None:
            return str(shard_id)
        return None


class AdminShardExtractor(BaseShardExtractor):
    """Extracts shard_id from a query parameter for admin use.

    Falls back to ?shard=east on the URL. Only intended for staff access.
    """

    def extract(self, request: HttpRequest) -> Optional[str]:
        from easyshard.settings import api_settings

        param = api_settings.ADMIN_SHARD_PARAM
        shard_id = request.GET.get(param)
        if shard_id is not None:
            return str(shard_id)
        return None
