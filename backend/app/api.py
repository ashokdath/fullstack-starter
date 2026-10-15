from typing import Any

from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.errors import AuthenticationError
from ninja.operation import Operation

from app.core.config import settings
from app.core.openapi import make_fastapi_compatible, operation_id
from app.items.routes import router as items_router
from app.users.login import router as login_router
from app.users.private import router as private_router
from app.users.routes import router as users_router
from app.utils_api.routes import router as utils_router


class API(NinjaAPI):
    def get_openapi_operation_id(self, operation: Operation) -> str:
        return operation_id(operation)

    def get_openapi_schema(self, **kwargs: Any) -> Any:
        schema = super().get_openapi_schema(**kwargs)
        return make_fastapi_compatible(
            schema, token_url=f"{settings.API_V1_STR}/login/access-token"
        )


api = API(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    urls_namespace="api",
)


@api.exception_handler(AuthenticationError)
def not_authenticated(request: HttpRequest, exc: AuthenticationError) -> HttpResponse:
    return api.create_response(request, {"detail": "Not authenticated"}, status=401)


api.add_router("/", login_router)
api.add_router("/users", users_router)
api.add_router("/utils", utils_router)
api.add_router("/items", items_router)

if settings.is_development:
    api.add_router("/private", private_router)
