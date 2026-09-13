import json
import logging

from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from easytenant.models import TenantConfig
from easytenant.settings import api_settings

logger = logging.getLogger("easytenant")


def _encrypt_for_transit(value: str) -> str:
    from cryptography.fernet import Fernet

    fernet = Fernet(api_settings.encryption_key)
    return fernet.encrypt(value.encode()).decode()


def _decrypt_from_db(value: str) -> str:
    return value


@csrf_exempt
@require_http_methods(["GET"])
def tenant_config_detail(request, tenant_id):
    """Return a single tenant's connection config (encrypted).

    GET /tenant-config/{tenant_id}/

    Requires Authorization: Bearer <service_token> header.
    The password is re-encrypted with the shared key for transit.
    """
    service_token = api_settings._get_raw_setting("SERVICE_TOKEN")
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[-1] if " " in auth_header else ""

    if not service_token or token != service_token:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        config = TenantConfig.objects.get(tenant_id=tenant_id, is_active=True)
    except TenantConfig.DoesNotExist:
        return JsonResponse({"error": "Tenant not found"}, status=404)

    data = {
        "tenant_id": config.tenant_id,
        "db_alias": config.db_alias,
        "engine": config.engine,
        "name": config.name,
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "password": _encrypt_for_transit(config.password),
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["POST"])
def reload_tenants(request):
    """Trigger a reload of tenant configurations.

    POST /tenants/reload/

    Requires X-Tenant-Reload-Secret header matching RELOAD_SECRET setting.
    """
    reload_secret = api_settings._get_raw_setting("RELOAD_SECRET")
    provided = request.headers.get("X-Tenant-Reload-Secret", "")

    if not reload_secret or provided != reload_secret:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    mode = api_settings._get_raw_setting("CONFIG_MODE") or "local"

    try:
        if mode == "local":
            from easytenant.connection_manager import reload as do_reload
        else:
            from easytenant.remote_connection_manager import reload as do_reload

        do_reload()
    except Exception as e:
        logger.error("Reload failed: %s", e)
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"status": "ok"})
