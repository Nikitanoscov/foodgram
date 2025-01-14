from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .constaints import (
    RECIPE_NAME_LENGTH,
    TAG_LENGTH,
    MEASUREMENT_LENGTH,
    MIN_VALIDATE_INTEGER,
    NAME_INGREDIENT,
    LEN_NAME
)
from .services.link_service import LinkService
from users.models import Users


class Ingredients(models.Model):
    """Модель ингредиентов."""

    name = models.TextField(
        max_length=NAME_INGREDIENT,
        unique=True,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'name',
                    'measurement_unit'
                ),
                name='unique_ingredient'
            ),
        )

    def __str__(self):
        return self.name[:LEN_NAME]


class Tags(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=TAG_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=TAG_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug[:LEN_NAME]


class Recipes(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.TextField(
        max_length=RECIPE_NAME_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes_media/',
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='RecipesIngredients',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tags,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        help_text='Введите время в минутах',
        validators=(MinValueValidator(MIN_VALIDATE_INTEGER),),
        verbose_name='Время приготовления'
    )
    pub_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации'
    )
    short_link = models.TextField(
        verbose_name='Короткая ссылка'
    )

    def save(self, *args, **kwargs):
        self.short_link = LinkService.generate_short_link()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:LEN_NAME]


class RecipesIngredients(models.Model):
    """Связная модель для определения ингредиентов рецепта."""

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='ingredients_for_recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='recipes_with_ingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        validators=(MinValueValidator(MIN_VALIDATE_INTEGER),),
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Рецепт Ингредиент'
        verbose_name_plural = 'Рецепты Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'recipe',
                    'ingredient'
                ),
                name='unique_recipe_ingredient'
            ),
        )

    def __str__(self):
        return (
            f'{self.recipe.name[:LEN_NAME]}-{self.ingredient.name[:LEN_NAME]}'
        )


class BaseUserRecipeRelation(models.Model):
    """Абстрактная модель для связи пользователь рецепт."""

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'user',
                    'recipe'
                ),
                name='unique_recipe_user_%(class)s'
            ),
        )

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.recipe.name[:LEN_NAME]} '
            f'({self._meta.verbose_name})'
        )


class Favourites(BaseUserRecipeRelation):
    """Модель для избранных рецептов."""

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCard(BaseUserRecipeRelation):
    """Модель для списка продуктов."""

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
