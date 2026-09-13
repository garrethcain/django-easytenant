from django.urls import include, path

urlpatterns = [
    path("", include("easytenant.urls")),
]
