from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validators import validate_username


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""
    username = models.CharField(
        'username',
        max_length=150,
        unique=True,
        validators=[validate_username, ]
    )
    first_name = models.CharField(
        'Имя',
        max_length=150
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )
    password = models.CharField(
        'Пароль',
        max_length=150,
        blank=False,
        null=False,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.username
