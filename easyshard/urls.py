from django.urls import path

from easyshard.views import reload_shards, shard_config_detail

app_name = "easyshard"

urlpatterns = [
    path("shard-config/<str:shard_id>/", shard_config_detail, name="shard-config-detail"),
    path("shards/reload/", reload_shards, name="reload-shards"),
]
