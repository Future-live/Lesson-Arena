from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "扩展信息",
            {
                "fields": (
                    "display_name",
                    "role",
                    "organization",
                    "title",
                    "bio",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "扩展信息",
            {
                "fields": ("email", "display_name", "role", "organization"),
            },
        ),
    )
    list_display = (
        "username",
        "display_name",
        "email",
        "role",
        "organization",
        "is_staff",
    )
    search_fields = ("username", "display_name", "email", "organization")
