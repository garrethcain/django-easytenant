from django.contrib import admin

from easyshard.models import ShardConfig


@admin.register(ShardConfig)
class ShardConfigAdmin(admin.ModelAdmin):
    list_display = ("shard_id", "db_alias", "host", "port", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("shard_id", "db_alias", "host", "name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Identity", {"fields": ("shard_id", "db_alias", "is_active")}),
        ("Connection", {"fields": ("engine", "name", "host", "port", "user", "password")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
