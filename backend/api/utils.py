from django.db.models import Sum
from django.http import HttpResponse
from recipes.models import RecipeIngredient, ShoppingCart
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class DownloadViewSet(APIView):
    """Вьюсет для загрузки списка покупок."""

    permission_classes = (IsAuthenticated,)

    def merge_shopping_cart(self):
        shopping_cart = ShoppingCart.objects.filter(
            user=self.request.user
        ).values('recipe')

        items = RecipeIngredient.objects.filter(
            recipe__in=shopping_cart
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        return items

    def get(self, request):
        items = self.merge_shopping_cart()
        text = ['Список покупок' + '\n' + '\n']
        for item in items:
            text.append(f"- {item['ingredient__name']} "
                        f"({item['ingredient__measurement_unit']}): "
                        f"{item['total_amount']}\n")

        response = HttpResponse(content_type='text/plain',
                                status=status.HTTP_200_OK)
        response['Content-Disposition'] = ('attachment; '
                                           'filename=shopping_cart.txt')
        response.writelines(text)
        return response
