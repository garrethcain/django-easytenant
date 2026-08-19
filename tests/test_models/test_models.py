import pytest

from easyshard.encrypted_fields import _get_fernet
from easyshard.models import ShardConfig


@pytest.mark.django_db
class TestShardConfig:
    def test_create_shard_config(self):
        from tests.conftest import make_shard_config

        config = make_shard_config(shard_id="east", db_alias="shard_east")
        assert config.pk is not None
        assert config.shard_id == "east"
        assert config.is_active is True

    def test_password_is_encrypted_in_db(self):
        from django.db import connection

        from tests.conftest import make_shard_config

        config = make_shard_config(
            shard_id="west",
            db_alias="shard_west",
            name="tenant_west",
            password="mysecret",
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password FROM easyshard_shardconfig WHERE id = %s",
                [config.pk],
            )
            row = cursor.fetchone()

        assert row[0] != "mysecret"
        assert row[0].startswith("gAAAAA")

        reloaded = ShardConfig.objects.get(pk=config.pk)
        assert reloaded.password == "mysecret"

    def test_to_connection_dict(self):
        from tests.conftest import make_shard_config

        config = make_shard_config(
            shard_id="north",
            db_alias="shard_north",
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
        config = ShardConfig(
            shard_id="east",
            db_alias="shard_east",
            name="tenant_east",
            host="localhost",
            port=5432,
            user="app",
            password="secret",
        )
        assert str(config) == "east → shard_east"

    def test_is_active_filtering(self):
        from tests.conftest import make_shard_config

        make_shard_config(shard_id="active", db_alias="shard_a", is_active=True)
        make_shard_config(shard_id="inactive", db_alias="shard_i", is_active=False)
        active = ShardConfig.objects.filter(is_active=True)
        assert active.count() >= 1
        assert "inactive" not in [s.shard_id for s in active]


class TestEncryptedCharField:
    def test_encrypt_decrypt_roundtrip(self):
        fernet = _get_fernet()
        plaintext = "super-secret-password"
        encrypted = fernet.encrypt(plaintext.encode()).decode()
        assert encrypted != plaintext
        decrypted = fernet.decrypt(encrypted.encode()).decode()
        assert decrypted == plaintext
