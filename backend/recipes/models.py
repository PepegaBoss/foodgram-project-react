from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель для тэгов"""
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        blank=False)
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        unique=True,
        default=None)
    slug = models.SlugField(
        'Слаг',
        max_length=200,
        unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов"""
    name = models.CharField(
        'Ингридиент',
        max_length=200)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=200)

    class Meta:
        db_table = 'ingredient'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipe',
        null=True)
    name = models.CharField(
        'Название рецепта',
        max_length=200,)
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes/',)
    text = models.TextField(
        'Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='RecipeIngredient',
        verbose_name='Ингредиент')
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэг')
    cooking_time = models.IntegerField(
        default=0,
        verbose_name='Время приготовления',
        validators=[MinValueValidator(0)])
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return self.name


class RecipeTag(models.Model):
    """Модель для связи тэгов с рецептами"""
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='тэг',
        related_name='recipetag')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=False,
        verbose_name='Рецепт',
        related_name='recipetag')

    class Meta:
        verbose_name = 'Рецепт/тэг'
        verbose_name_plural = 'Рецепты/тэги'
        constraints = [models.UniqueConstraint(
            fields=['tag', 'recipe'],
            name='unique_recipe_tag'
        )]

    def __str__(self) -> str:
        return f'{self.recipe} / {self.tag}'


class RecipeIngredient(models.Model):
    """Модель кол-ва ингридиетов в рецепте"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredient',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipeingredient',
        verbose_name='Ингредиент')
    amount = models.IntegerField(
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


class Favorite(models.Model):
    """Модель избранных рецептов"""
    user = models.ForeignKey(
        User,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Владелец')
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Понравившийся рецепт')

    class Meta:
        db_table = 'favorite'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self) -> str:
        return f'{self.recipe} добавлен в избранное.'


class ShoppingCart(models.Model):
    """Модель корзины для покупок"""
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Юзер')
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепты для покупок')

    class Meta:
        db_table = 'shopping_cart'
        verbose_name = 'Список покупок'

    def __str__(self) -> str:
        return f'{self.recipe} добавлен в корзину.'


class Follow(models.Model):
    """Модель подписок"""
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self) -> str:
        return f'{self.follower} подписан на {self.author}'
