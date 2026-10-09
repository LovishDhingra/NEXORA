from django.contrib import admin
from django.urls import include, path

from core.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/applications/", include("applications.urls")),
    path("api/cards/", include("cards.urls")),
]
