from rest_framework.response import Response
from rest_framework import status


class DisableHttpMethodsMixin:
    """Миксин для отключения определённых HTTP-методов"""

    def update(self, request, *args, **kwargs):
        """PUT method"""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        """POST method"""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        """DELETE method"""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
