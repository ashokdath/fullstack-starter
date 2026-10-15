from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from app.users.models import User


class UserCreationAdminForm(AdminUserCreationForm[User]):
    class Meta:
        model = User
        fields = ("email", "full_name")


class UserChangeAdminForm(UserChangeForm[User]):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin[User]):
    form = UserChangeAdminForm
    add_form = UserCreationAdminForm
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
    add_fieldsets = (
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
