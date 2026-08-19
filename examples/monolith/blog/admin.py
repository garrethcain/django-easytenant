from django.contrib import admin

from .models import BlogPost, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "shard_id", "is_active")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
