from django.urls import include, path

urlpatterns = [
    path("", include("easyshard.urls")),
]
