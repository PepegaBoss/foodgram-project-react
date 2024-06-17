import django_filters
from django_filters.rest_framework import BooleanFilter

from recipes.models import Ingredient, Recipe


class IngredientFilter(django_filters.FilterSet):
    """Для фильтрации по ингредиентам."""

    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    """
    Фильтр предназначен для запросов к объектам модели Recipe.
    Он позволяет фильтровать по slug тега, id автора,
    а также наличию в избранном и в списке покупок пользователя.
    """

    is_in_shopping_cart = BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_is_in_shopping_cart',)

    is_favorited = BooleanFilter(
        field_name='is_favorited',
        method='filter_is_favorited',)

    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug', lookup_expr='iexact')

    class Meta:
        model = Recipe
        fields = ('tags', 'is_in_shopping_cart', 'is_favorited', 'author')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        else:
            return queryset.exclude(shopping_cart__user=self.request.user)

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return queryset
        return queryset.filter(favorite__user=self.request.user)
