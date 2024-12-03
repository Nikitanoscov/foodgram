from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Введите корректное имя.'
)


class UsersManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(username, email, password, **extra_fields)


class CustomUsers(AbstractUser):
    """Кастомная модель User."""

    ROLES = (
        ('user', 'Пользователь'),
        ('admin', 'Админ')
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']    

    username = models.TextField(
        max_length=150,
        validators=[username_validator],
        unique=True
    )
    first_name = models.TextField(
        max_length=150
    )
    last_name = models.TextField(
        max_length=150
    )
    email = models.EmailField(
        max_length=254,
        unique=True
    )
    avatar = models.ImageField(
        upload_to='users_media/',
        default='backend/media/users_media/default_user_avatar.jpg'
    )
    role = models.CharField(
        verbose_name='Роль',
        choices=ROLES,
        max_length=20,
        default='user'
    )
    confirmation_code = models.CharField(max_length=100)

    objects = UsersManager()

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscribers(models.Model):
    """Модель для подписок."""
    author = models.ForeignKey(
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    subscriber = models.ForeignKey(
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='author'
    )
