from django.contrib import admin
from django.urls import path, re_path

from app.api import api
from app.core.config import settings
from app.core.views import spa_index

urlpatterns = [
    path(f"{settings.API_V1_STR.strip('/')}/", api.urls),
    path("admin/", admin.site.urls),
    # Everything else is a client-side route of the React app
    re_path(r"^(?!api/|admin/|static/).*$", spa_index, name="spa"),
]
