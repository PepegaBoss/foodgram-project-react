from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from api.utils import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для представления пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password', 'is_subscribed')
        read_only_fields = ('email', 'id', 'username',
                            'first_name', 'last_name',)
        extra_kwargs = {'password': {'write_only': True}, }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user or request.user.is_anonymous:
            return False
        user = request.user
        return Follow.objects.filter(follower=user, author=obj).exists()


class UserSignUpSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор Тегов."""

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов и ингридиентов."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all(),
        required=True,
    )
    name = serializers.CharField(source='ingredient.name',
                                 required=False)
    amount = serializers.IntegerField(required=True,
                                      allow_null=False,)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        required=False)

    unique_set = set()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, amount):
        if amount < 1:
            self.unique_set.clear()
            raise serializers.ValidationError(
                'Количество не может быть менее 1')
        return amount

    def validate(self, attrs):
        ingredient = attrs.get('ingredient').get('id').id
        if ingredient in self.unique_set:
            self.unique_set.clear()
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться!')
        self.unique_set.add(ingredient)
        return attrs


# Пробовал но не получилось разделить на 2 RecipeIngredientCreateSerializer,
# У меня рид не отображал кол-во ингридиентов
# а крейэт ругался что has no attribute 'unique_set'
# class RecipeIngredientReadSerializer(serializers.ModelSerializer):
#     """Сериализатор для чтения ингредиентов рецепта."""

#     id = serializers.ReadOnlyField(source='ingredient.id')
#     name = serializers.ReadOnlyField(source='ingredient.name',
#                                      required=False)
#     measurement_unit = serializers.CharField(
#                     source='ingredient.measurement_unit',
#                     required=False)

#     class Meta:
#         model = RecipeIngredient
#         fields = ('id', 'name', 'measurement_unit')


# class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
#     """Сериализатор для создания ингредиентов рецепта."""

#     id = serializers.PrimaryKeyRelatedField(
#         source='ingredient.id',
#         queryset=Ingredient.objects.all(),
#         required=True,
#     )
#     amount = serializers.IntegerField(required=True, allow_null=False)

#     class Meta:
#         model = RecipeIngredient
#         fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор информации о рецепте."""

    ingredients = RecipeIngredientCreateSerializer(source='recipeingredient',
                                                   many=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time',)
        read_only_fields = ('author',)
        model = Recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user and not request.user.is_anonymous:
            return Favorite.objects.filter(
                user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user and not request.user.is_anonymous:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = RecipeIngredientCreateSerializer(source='recipeingredient',
                                                   many=True,
                                                   required=True,
                                                   allow_null=False,)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text',
                  'cooking_time')
        model = Recipe

    def validate_ingredients(self, ingredients):
        RecipeIngredientCreateSerializer.unique_set.clear()
        if not ingredients:
            raise serializers.ValidationError(
                'Ингредиенты не могут отсутствовать.')
        return ingredients

    def validate_tags(self, tags):
        unique = set()
        for tag in tags:
            if tag.id in unique:
                raise serializers.ValidationError('tag не могут повторяться')
            unique.add(tag.id)
        return tags

    def validate(self, attrs):
        if 'tags' not in attrs:
            raise serializers.ValidationError(
                'Теги не могут отсутствовать')

        if 'recipeingredient' not in attrs:
            raise serializers.ValidationError(
                'Ингредиенты не могут отсутствовать')
        return attrs

    @staticmethod
    def create_ingredient(items, instance):
        ingredients = []
        for item in items:
            ingredients.append(
                RecipeIngredient(
                    recipe=instance,
                    ingredient=item.get('ingredient').get('id'),
                    amount=item['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(ingredients)

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('recipeingredient')
        request = self.context.get('request')
        validated_data['author'] = request.user
        instance = super().create(validated_data)
        self.create_ingredient(items, instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop('recipeingredient')
        instance.recipeingredient_set.clear()
        self.create_ingredient(items, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags,
            many=True,).data
        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавление в избранное."""

    name = serializers.StringRelatedField(source='recipe.name')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time',
                                            read_only=True)
    image = Base64ImageField(required=False,
                             allow_null=True,
                             source='recipe.image')

    class Meta:
        fields = ('user', 'recipe', 'id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
        model = Favorite

        extra_kwargs = {'user': {'write_only': True, 'required': False},
                        'recipe': {'write_only': True, 'required': False}}

    def validate(self, attrs):
        recipe_id = self.context.get(
            'request').parser_context.get('kwargs').get('title_id')
        recipe = Recipe.objects.filter(id=recipe_id).first()
        if not recipe:
            raise serializers.ValidationError('Рецепт не существует')
        user = self.context.get('request').user
        is_exists = Favorite.objects.filter(user=user,
                                            recipe=recipe).exists()
        if is_exists:
            raise serializers.ValidationError('Рецепт уже в избранном')
        attrs['recipe'] = recipe
        return attrs


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в подписки."""

    id = serializers.PrimaryKeyRelatedField(source='author',
                                            read_only=True)
    username = serializers.StringRelatedField(source='author.username')
    first_name = serializers.StringRelatedField(source='author.first_name')
    last_name = serializers.StringRelatedField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    email = serializers.StringRelatedField(source='author.email')

    class Meta:
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'recipes_count', 'recipes',)

        read_only_fields = ('email', 'id', 'username', 'first_name',
                            'last_name', 'is_subscribed', 'recipes',
                            'recipes_count',)
        model = Follow

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        return Follow.objects.filter(
            follower=request.user, author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request is None:
            return []
        limit = request.query_params.get('recipes_limit')
        recipes = obj.author.recipe.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = FollowSerializer(
            recipes,
            read_only=True,
            many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.recipe.all().count()

    def validate(self, attrs):
        author_id = int(self.context.get(
            'request').parser_context.get('kwargs').get('title_id'))
        user_id = self.context.get('request').user.id
        if author_id == user_id:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        if Follow.objects.filter(follower=user_id,
                                 author=author_id).exists():
            raise serializers.ValidationError('Вы уже подписаны на'
                                              ' этого автора')
        return attrs


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        fields = ('id',
                  'name',
                  'measurement_unit')
        model = Ingredient


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    id = serializers.PrimaryKeyRelatedField(
        source='recipe', read_only=True)
    name = serializers.StringRelatedField(
        source='recipe.name', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True)
    image = Base64ImageField(source='recipe.image', read_only=True)

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
        model = ShoppingCart

    def validate(self, attrs):
        recipe_id = self.context.get(
            'request').parser_context.get('kwargs').get('title_id')
        if not recipe_id:
            raise serializers.ValidationError('ID рецепта не указано в URL')
        recipes = Recipe.objects.filter(id=recipe_id)
        if not recipes.exists():
            raise serializers.ValidationError('Рецепт не существует')
        user = self.context.get('request').user
        recipe = recipes.first()
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в Списке покупок')
        return attrs

    def create(self, validated_data):
        user = self.context.get('request').user
        recipe_id = self.context.get(
            'request').parser_context.get('kwargs').get('title_id')
        recipe = Recipe.objects.get(id=recipe_id)
        shopping_cart = ShoppingCart.objects.create(user=user, recipe=recipe)
        return shopping_cart
