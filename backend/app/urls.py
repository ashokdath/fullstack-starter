from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from app.api import api
from app.core.config import settings

# API-only: the frontend is a separate app on the same domain, the proxy sends
# these paths here and everything else to it. Static and media files are
# served from object storage (see STORAGES in settings).
# The Django admin is not at /admin: that path is the frontend's admin page.
urlpatterns = [
    path(f"{settings.API_V1_STR.strip('/')}/", api.urls),
    path("django-admin/", admin.site.urls),
    # APPEND_SLASH is off, so redirect explicitly
    path("django-admin", RedirectView.as_view(url="/django-admin/", permanent=True)),
]
