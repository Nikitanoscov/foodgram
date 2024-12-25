from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import CustomUsers, Subscribers


@admin.register(CustomUsers)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        'avatar_tag',
        'email',
        'username'
    )

    fields = (
        'avatar',
        'email',
        'username'
    )
    search_fields = (
        'username',
        'email'
    )

    @admin.display(description='Аватар')
    def avatar_tag(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src={obj.avatar.url} width="80" height="60">'
            )
        return 'Без аватара'


@admin.register(Subscribers)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'subscriber'
    )
