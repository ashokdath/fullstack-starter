from app.items.models import Item
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_item() -> Item:
    user = create_random_user()
    return Item.objects.create(
        title=random_lower_string(),
        description=random_lower_string(),
        owner=user,
    )
