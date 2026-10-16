from django.contrib import admin
from unfold.admin import ModelAdmin

from app.items.models import Item


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ("title", "owner", "created_at")
    search_fields = ("title", "description", "owner__email")
    list_select_related = ("owner",)
    autocomplete_fields = ("owner",)
