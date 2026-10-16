from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from app.users.models import User

# Re-register the built-in Group admin with the Unfold theme
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class UserCreationAdminForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name")


class UserChangeAdminForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin[User], ModelAdmin):
    form = UserChangeAdminForm
    add_form = UserCreationAdminForm
    change_password_form = AdminPasswordChangeForm
    ordering = ("-created_at",)
    list_display = ("email", "full_name", "is_active", "is_superuser", "created_at")
    list_filter = ("is_active", "is_superuser")
    search_fields = ("email", "full_name")
    readonly_fields = ("created_at", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name",)}),
        ("Permissions", {"fields": ("is_active", "is_superuser")}),
        ("Dates", {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (  # type: ignore[assignment]  # Unfold types it as ()
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    filter_horizontal = ()
