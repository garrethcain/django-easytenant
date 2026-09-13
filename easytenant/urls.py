from django.urls import path

from easytenant.views import reload_tenants, tenant_config_detail

app_name = "easytenant"

urlpatterns = [
    path("tenant-config/<str:tenant_id>/", tenant_config_detail, name="tenant-config-detail"),
    path("tenants/reload/", reload_tenants, name="reload-tenants"),
]
