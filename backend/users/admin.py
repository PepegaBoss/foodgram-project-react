from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    """Кастомизация админки Пользователей."""

    list_display = ('username', 'email', )
    search_fields = ('username', "email", )


admin.site.register(User, CustomUserAdmin)
