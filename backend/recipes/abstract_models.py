from django.db import models

from .models import Recipes
from users.models import Users


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
                name='unique_recipe_user'
            ),
        )

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.recipe.name} '
            f'({self._meta.verbose_name})'
        )
