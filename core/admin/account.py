from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserModelAdmin
from django.contrib.auth.models import Group
from core.models import User


class UserAdmin(UserModelAdmin):
    model = User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('avatar', 'username', 'email', 'first_name', 'last_name', 'user_type', 'user_class', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'user_class', 'password1', 'password2',)}
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
