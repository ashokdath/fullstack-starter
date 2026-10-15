from django.http import HttpRequest
from ninja import Router

from app.users.models import User
from app.users.schemas import PrivateUserCreate, UserPublic

# Only mounted when ENVIRONMENT=development (see app.api), used by Playwright
router = Router(tags=["private"])


@router.post("/users/", response=UserPublic)
def create_user(request: HttpRequest, user_in: PrivateUserCreate) -> User:
    """
    Create a new user.
    """
    return User.objects.create_user(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    )
