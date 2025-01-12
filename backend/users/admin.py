from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import Users, Subscribers


@admin.register(Users)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'avatar_tag',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'count_recipes_tag',
        'count_subscriptions_tag'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'is_staff'
            ),
        }),
    )

    @admin.display(description='Аватар')
    def avatar_tag(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src={obj.avatar.url} width="80" height="60">'
            )
        return 'Без аватара'

    @admin.display(description='Количество рецептов')
    def count_recipes_tag(self, obj):
        return obj.recipes.all().count

    @admin.display(description='Количество подписок на автора')
    def count_subscriptions_tag(self, obj):
        return obj.user_subscriptions.all().count()


@admin.register(Subscribers)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'subscriber'
    )


admin.site.unregister(Group)
