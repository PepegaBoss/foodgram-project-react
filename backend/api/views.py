from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (FavoriteCreateSerializer, FollowCreateSerializer,
                             FollowReadSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagSerializer,
                             UserSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class UsersViewSet(DjoserUserViewSet):
    """Вьюсет для просмотра и редактирования данных пользователей."""
    serializer_class = UserSerializer
    queryset = DjoserUserViewSet.queryset

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request, *args, **kwargs):
        queryset = Follow.objects.filter(
            follower=self.request.user).prefetch_related('author__recipe')
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = FollowReadSerializer(
            paginated_queryset, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all().order_by('-pub_date')
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
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

    def add_to_collection(self, request, pk=None,
                          serializer_class=None):
        instance = self.get_object()
        data = {'user': request.user.id, 'recipe': instance.id}
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_collection(self, request, pk=None, model=None):
        instance = self.get_object()
        count, _ = model.objects.filter(
            user=request.user, recipe=instance).delete()
        if count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.add_to_collection(
            request, pk=pk, serializer_class=FavoriteCreateSerializer)

    @favorite.mapping.delete
    def remove_from_favorites(self, request, pk=None):
        return self.remove_from_collection(request, pk=pk, model=Favorite)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.add_to_collection(
            request, pk=pk, serializer_class=ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self.remove_from_collection(request, pk=pk, model=ShoppingCart)


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


class FollowViewSet(BaseViewset):
    """Вьюсет добавления в подписки."""

    serializer_class = FollowCreateSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post', 'delete']
    model = Follow
    user_model = User

    def perform_create(self, serializer):
        author = self._get_user()
        serializer.save(author=author)

    def create(self, request, *args, **kwargs):
        author = self._get_user()
        data = {'author': author.id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = FollowReadSerializer(
            serializer.instance, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED,
            headers=headers)

    @action(methods=['delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def delete(self, request, *args, **kwargs):
        author = self._get_user()
        model_items = self.model.objects.filter(
            author=author, follower=self.request.user)
        if model_items.exists():
            model_items.first().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            'Объект не существует.', status=status.HTTP_400_BAD_REQUEST)

    def _get_user(self):
        user_id = self.kwargs.get('user_id')
        try:
            return self.user_model.objects.get(pk=user_id)
        except self.user_model.DoesNotExist:
            raise Http404('Пользователь не найден')


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
