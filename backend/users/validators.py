from django.core.validators import RegexValidator


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Введите корректное имя.'
)
