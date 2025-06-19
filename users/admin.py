from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'dark_mode')
    list_filter = ('is_staff', 'is_superuser', 'dark_mode')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('dark_mode',)}),
    )
    inlines = (UserProfileInline,)
