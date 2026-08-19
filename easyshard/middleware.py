import logging

from easyshard.context import reset_shard_id, set_shard_id
from easyshard.extractors import AdminShardExtractor, BaseShardExtractor
from easyshard.settings import api_settings

logger = logging.getLogger("easyshard")


class ShardMiddleware:
    """Extracts shard_id from each request and sets it in the ContextVar.

    The extraction is delegated to the configured ID_EXTRACTOR (default: JWTShardExtractor).
    As a fallback for admin access, the ?shard= query param is checked.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._extractor: BaseShardExtractor = api_settings.ID_EXTRACTOR()
        self._admin_extractor = AdminShardExtractor()

    def __call__(self, request):
        shard_id = self._extractor(request)

        if shard_id is None:
            shard_id = self._admin_extractor(request)

        token = set_shard_id(shard_id)

        try:
            response = self.get_response(request)
        finally:
            reset_shard_id(token)

        return response
