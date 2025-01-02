from django.core.management.base import BaseCommand
from recipes.models import Ingredients
from django.core.serializers import serialize


class Command(BaseCommand):
    help = 'Создает бэкап данных из модели Ingredients'

    def handle(self, *args, **kwargs):

        queryset = Ingredients.objects.all()

        data = serialize('json', queryset)

        file_path = 'ingredients.json'
        with open(file_path, 'w', encoding='utf-8') as backup_file:
            backup_file.write(data)

        self.stdout.write(f'Бэкап модели Ingredients сохранен в "{file_path}"')
