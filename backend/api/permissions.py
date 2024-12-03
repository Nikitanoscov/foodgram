from rest_framework import permissions


class OnlyAuthorOrReadOnly(permissions.BasePermission):
    """Доступ к изменениям только автору."""
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.role == 'admin':
            return True
        if request.user.is_superuser:
            return True
        if obj.author == request.user:
            return True


class IsAdminOrSuperUser(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ
    только администраторам или суперпользователям.
    """
    def has_permission(self, request, view):
        user = request.user

        if user.is_authenticated:
            return user and (user.role == 'admin' or user.is_superuser)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return user and (user.role == 'admin' or user.is_superuser)