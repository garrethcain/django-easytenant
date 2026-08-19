import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def _get_fernet() -> Fernet:
    from easyshard.settings import api_settings

    return Fernet(api_settings.encryption_key)


class EncryptedCharField(models.CharField):
    """CharField with transparent Fernet encryption at rest."""

    description = "Fernet-encrypted string"

    def get_internal_type(self):
        return "TextField"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            fernet = _get_fernet()
            return fernet.decrypt(value.encode()).decode()
        except Exception:
            return value

    def to_python(self, value):
        if value is None or not isinstance(value, str):
            return value
        return value

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        if not isinstance(value, str):
            value = str(value)
        fernet = _get_fernet()
        return fernet.encrypt(value.encode()).decode()
