import pytest

from easytenant.encrypted_fields import _get_fernet
from easytenant.models import TenantConfig


@pytest.mark.django_db
class TestTenantConfig:
    def test_create_tenant_config(self):
        from tests.conftest import make_tenant_config

        config = make_tenant_config(tenant_id="east", db_alias="tenant_east")
        assert config.pk is not None
        assert config.tenant_id == "east"
        assert config.is_active is True

    def test_password_is_encrypted_in_db(self):
        from django.db import connection

        from tests.conftest import make_tenant_config

        config = make_tenant_config(
            tenant_id="west",
            db_alias="tenant_west",
            name="tenant_west",
            password="mysecret",
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password FROM easytenant_tenantconfig WHERE id = %s",
                [config.pk],
            )
            row = cursor.fetchone()

        assert row[0] != "mysecret"
        assert row[0].startswith("gAAAAA")

        reloaded = TenantConfig.objects.get(pk=config.pk)
        assert reloaded.password == "mysecret"

    def test_to_connection_dict(self):
        from tests.conftest import make_tenant_config

        config = make_tenant_config(
            tenant_id="north",
            db_alias="tenant_north",
            name="tenant_north",
            host="db.example.com",
            port=5433,
            user="dbuser",
            password="pass",
        )
        d = config.to_connection_dict()
        assert d["NAME"] == "tenant_north"
        assert d["HOST"] == "db.example.com"
        assert d["PORT"] == 5433
        assert d["USER"] == "dbuser"
        assert d["PASSWORD"] == "pass"

    def test_str_representation(self):
        config = TenantConfig(
            tenant_id="east",
            db_alias="tenant_east",
            name="tenant_east",
            host="localhost",
            port=5432,
            user="app",
            password="secret",
        )
        assert str(config) == "east → tenant_east"

    def test_is_active_filtering(self):
        from tests.conftest import make_tenant_config

        make_tenant_config(tenant_id="active", db_alias="tenant_a", is_active=True)
        make_tenant_config(tenant_id="inactive", db_alias="tenant_i", is_active=False)
        active = TenantConfig.objects.filter(is_active=True)
        assert active.count() >= 1
        assert "inactive" not in [s.tenant_id for s in active]


class TestEncryptedCharField:
    def test_encrypt_decrypt_roundtrip(self):
        fernet = _get_fernet()
        plaintext = "super-secret-password"
        encrypted = fernet.encrypt(plaintext.encode()).decode()
        assert encrypted != plaintext
        decrypted = fernet.decrypt(encrypted.encode()).decode()
        assert decrypted == plaintext
