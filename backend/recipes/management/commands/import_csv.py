import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла'

    def add_arguments(self, parser):
        project_root = Path(__file__).resolve(
        ).parent.parent.parent.parent
        data_root = project_root / 'data' / 'ingredients.csv'
        parser.add_argument(
            'csv_file',
            type=str,
            nargs='?',
            default=data_root,
            help='Укажите путь к CSV файлу. По умолчанию: data/ingredients.csv'
        )

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                self.stdout.write(f'Открываем файл: {csv_file_path}')
                csv_reader = csv.reader(file)
                ingredients = []
                for name, unit in csv_reader:
                    if name and unit:
                        ingredients.append(Ingredients(
                            name=name,
                            measurement_unit=unit,
                        ))
                    else:
                        continue

                Ingredients.objects.bulk_create(
                    ingredients,
                    ignore_conflicts=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        'Данные успешно импортированы.'
                    )
                )

        except FileNotFoundError:
            raise CommandError(
                f'Файл {csv_file_path} не найден. '
                'Убедитесь, что путь указан правильно.'
            )
        except Exception as e:
            raise CommandError(f'Произошла ошибка: {e}')
