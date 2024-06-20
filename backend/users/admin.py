from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    """Кастомизация админки Пользователей."""

    list_display = ('username', 'email', )
    search_fields = ('username', "email", )


admin.site.register(User, UserAdmin)
