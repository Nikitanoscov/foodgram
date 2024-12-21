import io

from rest_framework.renderers import BaseRenderer


class TextShoppingCartRenders(BaseRenderer):

    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        text_buffer = io.StringIO()
        for recipes_data in data:
            text_buffer.write(recipes_data.get('recipe_name') + '\n')
            text_buffer.write(
                '\n'.join(
                    f"{ingredient.get('name')} - {ingredient.get('amount')}"
                    for ingredient in recipes_data.get('ingredients')
                )
            )
            text_buffer.write('\n\n\n')
        return text_buffer.getvalue()
