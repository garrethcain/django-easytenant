from django.contrib import admin

from easytenant.models import TenantConfig


@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    list_display = ("tenant_id", "db_alias", "host", "port", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("tenant_id", "db_alias", "host", "name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Identity", {"fields": ("tenant_id", "db_alias", "is_active")}),
        ("Connection", {"fields": ("engine", "name", "host", "port", "user", "password")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
