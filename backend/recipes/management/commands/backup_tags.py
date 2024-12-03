import json
from django.core.management.base import BaseCommand
from recipes.models import Tags
from django.core.serializers import serialize


class Command(BaseCommand):
    help = 'Создает бэкап данных из модели YourModel'

    def handle(self, *args, **kwargs):

        queryset = Tags.objects.all()

        data = serialize('json', queryset)

        file_path = 'tags.json'
        with open(file_path, 'w', encoding='utf-8') as backup_file:
            backup_file.write(data)

        self.stdout.write(f'Бэкап модели YourModel сохранен в "{file_path}"')