from django.core.management.base import BaseCommand
from django.core.serializers import serialize

from recipes.models import Tags


class Command(BaseCommand):
    help = 'Создает бэкап данных из модели Tag'

    def handle(self, *args, **kwargs):

        queryset = Tags.objects.all()

        data = serialize('json', queryset)

        file_path = 'tags.json'
        with open(file_path, 'w', encoding='utf-8') as backup_file:
            backup_file.write(data)

        self.stdout.write(f'Бэкап модели Tag сохранен в "{file_path}"')
