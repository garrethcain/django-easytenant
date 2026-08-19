import pytest

from easyshard.checks import check_shard_settings


class TestChecks:
    def test_no_warnings_with_full_config(self, settings):
        settings.EASY_SHARD = {
            "CONFIG_MODE": "local",
            "ENCRYPTION_KEY": "Y2hhbmdlLW1lLXByb2R1Y3Rpb24ta2V5LTMyLWJ5dGVzIQ==",
        }
        from easyshard.settings import api_settings

        api_settings.reload()
        errors = check_shard_settings(None)
        assert errors == []

    def test_warning_missing_encryption_key(self, settings):
        settings.EASY_SHARD = {"CONFIG_MODE": "local"}
        from easyshard.settings import api_settings

        api_settings.reload()
        errors = check_shard_settings(None)
        ids = [e.id for e in errors]
        assert "easyshard.W003" in ids

    def test_remote_mode_warnings(self, settings):
        settings.EASY_SHARD = {"CONFIG_MODE": "remote"}
        from easyshard.settings import api_settings

        api_settings.reload()
        errors = check_shard_settings(None)
        ids = [e.id for e in errors]
        assert "easyshard.W001" in ids
        assert "easyshard.W002" in ids

    def test_remote_mode_no_warnings_when_configured(self, settings):
        settings.EASY_SHARD = {
            "CONFIG_MODE": "remote",
            "REMOTE_SHARD_CONFIG_URL": "https://auth.example.com",
            "SERVICE_TOKEN": "secret-token",
            "ENCRYPTION_KEY": "Y2hhbmdlLW1lLXByb2R1Y3Rpb24ta2V5LTMyLWJ5dGVzIQ==",
        }
        from easyshard.settings import api_settings

        api_settings.reload()
        errors = check_shard_settings(None)
        assert errors == []
