from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Введите корректное имя.'
)


class CustomUsers(AbstractUser):
    """Кастомная модель User."""

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    username = models.TextField(
        max_length=150,
        validators=[username_validator],
        unique=True,
        verbose_name='Пользовательское имя'
    )
    first_name = models.TextField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.TextField(
        max_length=150,
        verbose_name='Фамилия'
    )
    email = models.EmailField(
        max_length=254,
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
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    subscriber = models.ForeignKey(
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        unique_together = (
            'author',
            'subscriber'
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
        return f"{self.author} - {self.subscriber}"
