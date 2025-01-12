import uuid


class LinkService:
    """Сервис для создание коротких ссылок."""

    @staticmethod
    def generate_short_link():
        short_link = uuid.uuid4().hex[:5]
        return f'{short_link}'
