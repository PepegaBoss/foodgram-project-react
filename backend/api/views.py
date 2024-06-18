from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, UserSerializer)

User = get_user_model()


class UsersViewSet(DjoserUserViewSet):
    """Вьюсет для просмотра и редактирования данных пользователей."""
    serializer_class = UserSerializer
    queryset = DjoserUserViewSet.queryset

    def get_permissions(self):
        if self.action == 'me':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all().order_by('-pub_date')
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.user.is_anonymous:
            return RecipeSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _delete_object(self, request, model, object_id):
        obj = get_object_or_404(model, pk=object_id)
        if not self.request.user == obj.user:
            return Response(
                "У вас нет прав для выполнения этого действия.",
                status=status.HTTP_403_FORBIDDEN)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Сделал так но че то сайт перестал работать, если удаляю из утилс
    # urls пробовал менять не помогло
    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def generate_shopping_cart_file(self, request):
        shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user).values('recipe')
        items = RecipeIngredient.objects.filter(
            recipe__in=shopping_cart).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        text = ['Список покупок' + '\n' + '\n']
        for item in items:
            text.append(f"- {item['ingredient__name']} "
                        f"({item['ingredient__measurement_unit']}): "
                        f"{item['total_amount']}\n")
        response = HttpResponse(
            content_type='text/plain', status=status.HTTP_200_OK)
        response['Content-Disposition'] = ('attachment; '
                                           'filename=shopping_cart.txt')
        response.writelines(text)
        return response


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет для тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly)
    http_method_names = ['get']
    pagination_class = None


class BaseViewset(viewsets.ModelViewSet):
    """Набор базовых представлений для управления"""
    """подписками, избранным и списком покупок."""

    def _get_title_id(self):
        return self.kwargs.get('title_id')

    def _get_title(self, title_model):
        return get_object_or_404(title_model, id=self._get_title_id())

    def perform_create(self, serializer):
        recipe = self._get_title(self.title_model)
        serializer.save(user=self.request.user,
                        recipe=recipe,)

    @action(methods=['delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def delete(self, request, *args, **kwargs):
        recipe = self._get_title(self.title_model)
        model_item = get_object_or_404(
            self.model, recipe=recipe, user=self.request.user)
        model_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(BaseViewset):
    """Вьюсет списка покупок."""

    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post', 'delete']
    model = ShoppingCart
    title_model = Recipe


class FavoriteViewSet(BaseViewset):
    """Вьюсет добавления в избранное."""

    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    model = Favorite
    title_model = Recipe
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post', 'delete']
    lookup_field = 'id'


class FollowViewSet(BaseViewset):
    """Вьюсет добавления в подписки."""

    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post', 'delete']
    model = Follow
    title_model = User

    def perform_create(self, serializer):
        author = self._get_title(self.title_model)
        serializer.save(follower=self.request.user,
                        author=author,)

    def create(self, request, *args, **kwargs):
        author = self._get_title(self.title_model)
        data = {'author': author}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['delete'],
            detail=True,
            permission_classes=[IsAuthenticated])
    def delete(self, request, *args, **kwargs):
        author = self._get_title(self.title_model)
        model_items = self.model.objects.filter(author=author,
                                                follower=self.request.user)
        if model_items.exists():
            model_items.first().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response('Объект не существует.',
                        status=status.HTTP_400_BAD_REQUEST)


class FollowListViewSet(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """Вьюсет списка подписок."""

    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Follow.objects.filter(
                follower=self.request.user).prefetch_related('author__recipe'))


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет просмотра ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    filterset_fields = ('name',)
