from django.contrib.auth.models import AbstractUser
from django.db import models

from easyshard.models import ShardUserMixin


class User(ShardUserMixin, AbstractUser):
    """Custom user with shard_id assignment.

    Users on 'trial' share the shard_trial database.
    Users on 'enterprise' get their own shard_enterprise database.
    """


class BlogPost(models.Model):
    """A simple model that lives on the user's shard database."""

    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
