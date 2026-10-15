import uuid

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError

from app.core.security import current_user, jwt_auth
from app.items.models import Item
from app.items.schemas import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from app.schemas import Message

router = Router(tags=["items"], auth=jwt_auth)


def get_owned_item(request: HttpRequest, id: uuid.UUID) -> Item:
    item = Item.objects.filter(pk=id).first()
    if not item:
        raise HttpError(404, "Item not found")
    user = current_user(request)
    if not user.is_superuser and item.owner_id != user.id:
        raise HttpError(403, "Not enough permissions")
    return item


@router.get("/", response=ItemsPublic)
def read_items(request: HttpRequest, skip: int = 0, limit: int = 100) -> ItemsPublic:
    """
    Retrieve items.
    """
    user = current_user(request)
    items = Item.objects.order_by("-created_at")
    if not user.is_superuser:
        items = items.filter(owner=user)
    return ItemsPublic(
        data=[ItemPublic.model_validate(i) for i in items[skip : skip + limit]],
        count=items.count(),
    )


@router.get("/{uuid:id}", response=ItemPublic)
def read_item(request: HttpRequest, id: uuid.UUID) -> Item:
    """
    Get item by ID.
    """
    return get_owned_item(request, id)


@router.post("/", response=ItemPublic)
def create_item(request: HttpRequest, item_in: ItemCreate) -> Item:
    """
    Create new item.
    """
    return Item.objects.create(owner=current_user(request), **item_in.model_dump())


@router.put("/{uuid:id}", response=ItemPublic)
def update_item(request: HttpRequest, id: uuid.UUID, item_in: ItemUpdate) -> Item:
    """
    Update an item.
    """
    item = get_owned_item(request, id)
    for field, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.save()
    return item


@router.delete("/{uuid:id}", response=Message)
def delete_item(request: HttpRequest, id: uuid.UUID) -> Message:
    """
    Delete an item.
    """
    get_owned_item(request, id).delete()
    return Message(message="Item deleted successfully")
