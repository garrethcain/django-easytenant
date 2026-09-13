from django.contrib.auth.models import AbstractUser
from django.db import models

from easytenant.models import TenantUserMixin


class User(TenantUserMixin, AbstractUser):
    """Custom user with tenant_id assignment.

    Users on 'trial' share the tenant_trial database.
    Users on 'enterprise' get their own tenant_enterprise database.
    """


class BlogPost(models.Model):
    """A simple model that lives on the user's tenant database."""

    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
