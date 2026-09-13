from django.db import models
from django.utils.translation import gettext_lazy as _

from easytenant.encrypted_fields import EncryptedCharField


class TenantConfig(models.Model):
    """Stores database connection details for each tenant.

    Lives on the 'default' database (auth service or monolith).
    The TenantRouter always routes queries for this model to 'default'.
    """

    tenant_id = models.CharField(
        _("tenant ID"),
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Unique identifier for this tenant, matching the JWT claim value."),
    )
    db_alias = models.CharField(
        _("database alias"),
        max_length=64,
        unique=True,
        help_text=_("The Django DATABASES key this tenant maps to (e.g. 'tenant_east')."),
    )
    engine = models.CharField(
        _("engine"),
        max_length=128,
        default="django.db.backends.postgresql",
    )
    name = models.CharField(_("database name"), max_length=128)
    host = models.CharField(_("host"), max_length=256)
    port = models.IntegerField(_("port"))
    user = models.CharField(_("user"), max_length=128)
    password = EncryptedCharField(
        _("password"),
        max_length=256,
        help_text=_("Stored encrypted at rest using Fernet."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
        help_text=_("Inactive tenants reject new requests with a 500 error."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("tenant config")
        verbose_name_plural = _("tenant configs")
        db_table = "easytenant_tenantconfig"
        ordering = ["tenant_id"]

    def __str__(self):
        return f"{self.tenant_id} → {self.db_alias}"

    def to_connection_dict(self) -> dict:
        """Return Django DATABASES-style connection dict."""
        return {
            "ENGINE": self.engine,
            "NAME": self.name,
            "HOST": self.host,
            "PORT": self.port,
            "USER": self.user,
            "PASSWORD": self.password,
        }


class TenantUserMixin(models.Model):
    """Abstract mixin that adds a tenant_id field to a User model.

    Users add this to their custom User model:

        class User(TenantUserMixin, AbstractUser):
            ...
    """

    tenant_id = models.CharField(
        _("tenant ID"),
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Which database tenant this user's data lives on."),
    )

    class Meta:
        abstract = True
