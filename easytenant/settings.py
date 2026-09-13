from django.conf import settings
from django.test.signals import setting_changed

DEFAULTS = {
    "ID_EXTRACTOR": "easytenant.extractors.JWTTenantExtractor",
    "ID_JWT_CLAIM": "tenant_id",
    "ID_HEADER_NAME": "X-Tenant-Id",
    "CONFIG_MODE": "local",
    "DB_RESOLVER": "easytenant.connection_manager.resolve_db",
    "MIDDLEWARE_VERIFY_TOKEN": True,
    "JWT_ALGORITHM": "HS256",
    "JWT_SIGNING_KEY": None,
    "ENCRYPTION_KEY": None,
    "RELOAD_SECRET": None,
    "CACHE_TTL": 300,
    "SERVICE_TOKEN": None,
    "REMOTE_TENANT_CONFIG_URL": None,
    "REMOTE_TENANT_CONFIG_PATH": "/tenant-config/",
    "ADMIN_TENANT_PARAM": "tenant",
}

IMPORT_STRINGS = [
    "ID_EXTRACTOR",
    "DB_RESOLVER",
]

REMOVED_SETTINGS = ["TENANTED_APPS"]


class APISettings:
    def __init__(self, user_settings: dict | None, defaults: dict, import_strings: list):
        self._user_settings = user_settings
        self.defaults = defaults
        self.import_strings = import_strings
        self._cached_attrs: set[str] = set()

    @property
    def user_settings(self) -> dict:
        if not hasattr(self, "_cached_user_settings"):
            self._cached_user_settings = getattr(settings, "EASY_TENANT", {})
        return self._cached_user_settings

    def __getattr__(self, attr: str):
        if attr not in self.defaults:
            raise AttributeError(f"Invalid setting: '{attr}'")

        try:
            value = self.user_settings[attr]
        except KeyError:
            value = self.defaults[attr]

        if attr in self.import_strings:
            value = self._perform_import(value, attr)

        self._cached_attrs.add(attr)
        setattr(self, attr, value)
        return value

    @property
    def encryption_key(self):
        """Encryption key with fallback to SECRET_KEY-derived key."""
        key = self._get_raw_setting("ENCRYPTION_KEY")
        if key is not None:
            return key

        from django.conf import settings as django_settings

        secret = django_settings.SECRET_KEY
        import hashlib

        derived = hashlib.pbkdf2_hmac("sha256", secret.encode(), b"easytenant-salt", 480000)
        import base64

        return base64.urlsafe_b64encode(derived)

    def _get_raw_setting(self, attr: str):
        try:
            return self.user_settings[attr]
        except KeyError:
            return self.defaults.get(attr)

    def _perform_import(self, value, setting_name: str):
        if value is None:
            return None
        if isinstance(value, str):
            return self._import_from_string(value, setting_name)
        if isinstance(value, (list, tuple)):
            return [self._import_from_string(item, setting_name) for item in value]
        return value

    @staticmethod
    def _import_from_string(value: str, setting_name: str):
        from importlib import import_module

        try:
            module_path, class_name = value.rsplit(".", 1)
            module = import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Could not import '{value}' for setting '{setting_name}'. {e.__class__.__name__}: {e}."
            )

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_cached_user_settings"):
            del self._cached_user_settings


USER_SETTINGS = getattr(settings, "EASY_TENANT", None)

api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(*args, **kwargs):
    setting = kwargs.get("setting")
    if setting == "EASY_TENANT":
        api_settings.reload()


setting_changed.connect(reload_api_settings)
