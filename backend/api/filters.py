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
        if self.request.user.is_authenticated and value:
            return queryset.filter(
                shoppingcart_relations__user=self.request.user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(
                favorite_relations__user=self.request.user)
        return queryset
