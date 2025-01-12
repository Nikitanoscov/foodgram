from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

from .constaints import EMAIL_LENGTH, NAME_LENGTH
from .validators import username_validator


class Users(AbstractUser):
    """Кастомная модель User."""

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )

    username = models.TextField(
        max_length=NAME_LENGTH,
        validators=[username_validator],
        unique=True,
        verbose_name='Пользовательское имя'
    )
    first_name = models.TextField(
        max_length=NAME_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.TextField(
        max_length=NAME_LENGTH,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        verbose_name='Почта'
    )
    avatar = models.ImageField(
        upload_to='users_media/',
        null=True,
        verbose_name='Аватар'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribers(models.Model):
    """Модель для подписок."""

    author = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='subscriptions_to_author',
        verbose_name='Автор'
    )
    subscriber = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_subscriptions',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'author',
                    'subscriber'
                ),
                name='unique_subscription'
            ),
        )

    def clean(self):
        if self.author == self.subscriber:
            raise ValidationError(
                ('Пользователь не может подписаться сам на себя.')
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.author} - {self.subscriber}'
