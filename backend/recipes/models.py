from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from api.constants import RECIPE_MODELS_MAX_LENGTH, TAG_MAX_LEN

User = get_user_model()


class Tag(models.Model):

    """Модель для тэгов"""
    name = models.CharField(
        'Название',
        max_length=TAG_MAX_LEN,
        unique=True,
    )
    color = ColorField(
        verbose_name='Цвет',
        default='#FFFFFF',
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=TAG_MAX_LEN,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):

    """Модель ингредиентов"""
    name = models.CharField(
        'Ингредиент',
        max_length=RECIPE_MODELS_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=RECIPE_MODELS_MAX_LENGTH
    )

    class Meta:
        db_table = 'ingredient'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipe',
        null=True
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200,
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes/',
    )
    text = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='RecipeIngredient',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэг'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.name


class RecipeIngredient(models.Model):
    """Модель кол-ва ингридиетов в рецепте"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredient',
        verbose_name='Рецепт'

    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipeingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                1, 'Количество ингредиентов не может быть меньше 1'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        unique_together = ('recipe', 'ingredient')
        ordering = ['recipe', 'ingredient']


class BaseUserRecipeRelation(models.Model):
    """Базовая абстрактная модель для отношения пользователь-рецепт"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ['user', 'recipe']

    def __str__(self) -> str:
        return f'{self.recipe} добавлен пользователем {self.user}.'


class Favorite(BaseUserRecipeRelation):
    """Модель избранных рецептов"""

    class Meta(BaseUserRecipeRelation.Meta):
        db_table = 'favorite'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self) -> str:
        return f'{self.recipe} добавлен в избранное пользователем {self.user}.'


class ShoppingCart(BaseUserRecipeRelation):
    """Модель корзины для покупок"""

    class Meta(BaseUserRecipeRelation.Meta):
        db_table = 'shopping_cart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart_user_recipe')
        ]

    def __str__(self) -> str:
        return f'{self.recipe} добавлен в корзину пользователем {self.user}.'
