import io

from rest_framework.renderers import BaseRenderer


class TextShoppingCartRenders(BaseRenderer):

    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        text_buffer = io.StringIO()
        result = {}
        for recipes_data in data:
            for key, value in recipes_data.items():
                if key in result.keys():
                    result[key] += value
                else:
                    result[key] = value
        text_buffer.write(
            '\n'.join(
                f"{key} - {value}"
                for key, value in result.items()
            )
        )
        return text_buffer.getvalue()
