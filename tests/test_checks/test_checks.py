import pytest

from easytenant.checks import check_tenant_settings


class TestChecks:
    def test_no_warnings_with_full_config(self, settings):
        settings.EASY_TENANT = {
            "CONFIG_MODE": "local",
            "ENCRYPTION_KEY": "Y2hhbmdlLW1lLXByb2R1Y3Rpb24ta2V5LTMyLWJ5dGVzIQ==",
        }
        from easytenant.settings import api_settings

        api_settings.reload()
        errors = check_tenant_settings(None)
        assert errors == []

    def test_warning_missing_encryption_key(self, settings):
        settings.EASY_TENANT = {"CONFIG_MODE": "local"}
        from easytenant.settings import api_settings

        api_settings.reload()
        errors = check_tenant_settings(None)
        ids = [e.id for e in errors]
        assert "easytenant.W003" in ids

    def test_remote_mode_warnings(self, settings):
        settings.EASY_TENANT = {"CONFIG_MODE": "remote"}
        from easytenant.settings import api_settings

        api_settings.reload()
        errors = check_tenant_settings(None)
        ids = [e.id for e in errors]
        assert "easytenant.W001" in ids
        assert "easytenant.W002" in ids

    def test_remote_mode_no_warnings_when_configured(self, settings):
        settings.EASY_TENANT = {
            "CONFIG_MODE": "remote",
            "REMOTE_TENANT_CONFIG_URL": "https://auth.example.com",
            "SERVICE_TOKEN": "secret-token",
            "ENCRYPTION_KEY": "Y2hhbmdlLW1lLXByb2R1Y3Rpb24ta2V5LTMyLWJ5dGVzIQ==",
        }
        from easytenant.settings import api_settings

        api_settings.reload()
        errors = check_tenant_settings(None)
        assert errors == []
