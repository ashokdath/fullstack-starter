from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponseNotFound
from django.http.response import HttpResponseBase


def spa_index(request: HttpRequest) -> HttpResponseBase:
    """Serve the React app's index.html; TanStack Router resolves the path."""
    index = settings.FRONTEND_DIR / "index.html"
    if not index.is_file():
        return HttpResponseNotFound("Frontend not built")
    return FileResponse(index.open("rb"), content_type="text/html")
