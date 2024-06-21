import csv

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Скрипт импорта из файла .csv"""

    def handle(self, *args, **kwargs):
        model = Ingredient
        ingredients = []

        with open(
            f'{settings.BASE_DIR}/data/ingredients.csv',
            newline='',
            encoding='utf-8'
        ) as csv_file:
            reader = csv.reader(csv_file)
            count = 0

            for row in reader:
                name, unit = row
                ingredients.append(model(name=name, measurement_unit=unit))
                count += 1

            model.objects.bulk_create(ingredients)

            print(f'Обработано: {count} записей.')

        self.stdout.write(self.style.SUCCESS('Данные загружены'))
