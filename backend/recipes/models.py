from datetime import datetime
import uuid

from django.core.validators import MinValueValidator
from django.db import models

from backend.settings import SITE_URL
from users.models import CustomUsers


class Ingredients(models.Model):
    """Модель ингредиентов."""
    name = models.TextField(
        max_length=50,
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=10
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Игредиенты'

    def __str__(self):
        return self.name


class Tags(models.Model):
    """Модель тегов."""
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=32, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Recipes(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='recipes',
        null=False
    )
    name = models.TextField(
        max_length=256,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes_media/',
        blank=True
    )
    text = models.TextField(
        max_length=200,
        blank=True
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='RecipesIngredients',
        blank=True,
    )
    tags = models.ManyToManyField(
        Tags,
        through='RecipesTags',
        blank=True
    )
    cooking_time = models.IntegerField(
        help_text='Введите время в минутах',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        default=datetime.now
    )
    short_link = models.TextField(
        blank=True
    )

    def save(self, *args, **kwargs):
        self.short_link = self.generate_short_link()
        return super().save(*args, **kwargs)

    def generate_short_link(self):
        short_link = uuid.uuid4().hex[:5]
        return f"s/{short_link}"

    def get_full_short_link(self, request=None):
        if request:
            domain = request.get_host()
        else:
            domain = SITE_URL
        return f"https://{domain}recipes/{self.short_link}"

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return (
            f'Рецепт {self.name},'
            f'из {self.ingredients},'
            f'под тегами {self.tags}'
        )


class RecipesIngredients(models.Model):
    """Связная модель для определения ингредиентов рецепта."""
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='recipe'
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class RecipesTags(models.Model):
    """Модель для связи рецептов и тегов."""
    recipe = models.ForeignKey(
        Recipes,
        related_name='tag',
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tags,
        related_name='recipe_for_tag',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'


class Favourites(models.Model):
    """Модель для избранных рецептов."""
    user = models.ForeignKey(
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='favorite_recipe'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='user'
    )


class ShoppingCard(models.Model):
    """Модель для списка продуктов."""
    user = models.ForeignKey(
        CustomUsers,
        on_delete=models.CASCADE,
        related_name='shopping_recipe'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='user_is_shopping'
    )
