from rest_framework import permissions


class OnlyAuthorOrReadOnly(permissions.BasePermission):
    """Доступ к изменениям только автору."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            or request.method in permissions.SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
