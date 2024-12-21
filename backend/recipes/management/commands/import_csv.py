import csv

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredients


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Укажите путь к CSV файлу'
        )

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                self.stdout.write(f'Открываем файл: {csv_file_path}')
                csv_reader = csv.reader(file)

                count = 0
                for row in csv_reader:
                    try:
                        Ingredients.objects.create(
                            name=row[0],
                            measurement_unit=row[1],
                        )
                        count += 1
                    except Exception as e:
                        self.stderr.write(f"Ошибка при создании записи: {e}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно импортировано {count} записей'
                    )
                )

        except FileNotFoundError:
            raise CommandError(
                f'Файл {csv_file_path} не найден.'
                ' Убедитесь, что путь указан правильно.'
            )
        except Exception as e:
            raise CommandError(f'Произошла ошибка: {e}')
