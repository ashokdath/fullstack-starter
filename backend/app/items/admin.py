from django.contrib import admin

from app.items.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin[Item]):
    list_display = ("title", "owner", "created_at")
    search_fields = ("title", "description", "owner__email")
    list_select_related = ("owner",)
    autocomplete_fields = ("owner",)
