from typing import Any

from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate


def create_user(*, user_create: UserCreate) -> User:
    data = user_create.model_dump(exclude={"password"})
    return User.objects.create_user(password=user_create.password, **data)


def update_user(*, db_user: User, user_in: UserUpdate) -> User:
    user_data: dict[str, Any] = user_in.model_dump(exclude_unset=True)
    password = user_data.pop("password", None)
    for field, value in user_data.items():
        setattr(db_user, field, value)
    if password:
        db_user.set_password(password)
    db_user.save()
    return db_user


def get_user_by_email(*, email: str) -> User | None:
    return User.objects.filter(email=email).first()


def authenticate(*, email: str, password: str) -> User | None:
    db_user = get_user_by_email(email=email)
    if not db_user:
        # Timing attack prevention: an unusable password still runs the default
        # hasher once, so unknown emails take as long as wrong passwords
        User().check_password(password)
        return None
    # `check_password` also upgrades the stored hash when the hasher changes
    if not db_user.check_password(password):
        return None
    return db_user
