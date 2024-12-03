from rest_framework import status
from rest_framework.response import Response
import djoser.views
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.pagination import LimitOffsetPagination







from .serializers import (
    AvatarSerializer,
    UsersCreateSerializers,
    UserSerializer
)
from .models import CustomUsers
from api.permissions import OnlyAuthorOrReadOnly


class UserViewSet(djoser.views.UserViewSet):
    queryset = CustomUsers.objects.all()
    serializer_class = UserSerializer
    permission_class = (AllowAny,)
    # filter_backends = [DjangoFilterBackend]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        if self.action == 'list':
            return CustomUsers.objects.all()
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        qs = self.queryset
        print(qs)
        return super().list(request, *args, **kwargs)

    def update_avatar(self, request):
        try:
            user = request.user
            avatar = request.data.get('avatar')
            serializer = AvatarSerializer(
                data=request.data,
                instance=user
            )
            if serializer.is_valid():
                serializer.save()
                message = {avatar: user.avatar}
                return Response(message, status=status.HTTP_200_OK)
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка при обновлении аватара: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete_avatar(self, request):
        try:
            user = request.user
            user.avatar = 'backend/media/users_media/default_user_avatar.jpg'
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": f"Ошибка при удалении аватара: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_class=(OnlyAuthorOrReadOnly,)
    )
    def me_avatar(self, request):
        if request.method == 'PUT':
            return self.update_avatar(request=request)
        return self.delete_avatar(request=request)

    
    # @action(methods=['PUT'], detail=)
    # def update_avatar(self, request):



# class UserViewSet(viewsets.ModelViewSet):
#     queryset = CustomUsers.objects.all()
#     serializer_class = UserSerializer

#     def get_serializer(self, *args, **kwargs):
#         if self.action == 'create':
#             return UsersCreateSerializers
#         return super().get_serializer(*args, **kwargs)



    
