import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import CustomUsers, Subscribers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UsersCreateSerializers(serializers.ModelSerializer):

    class Meta:
        model = CustomUsers
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = (
            'id',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUsers.objects.create(**validated_data)
        user.set_password(password)  # Захешировать пароль
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(
        'get_avatar'
    )

    class Meta:
        model = CustomUsers
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribers.objects.filter(
                subscriber=request.user, author=obj
            ).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = CustomUsers
        fields = ('avatar',)


class SubscribeSerializers(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='recipe.id'
    )

    class Meta:
        model = Subscribers
        fields = (
            'email',
            'id',
            'name',
            'image',
            'cooking_time'
        )
