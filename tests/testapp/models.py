from django.db import models


class BlogPost(models.Model):
    """A simple model that will be routed to shard databases."""

    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "testapp"
        db_table = "blog_post"

    def __str__(self):
        return self.title
