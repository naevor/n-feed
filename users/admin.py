from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Profile", {"fields": ("bio", "avatar", "following")}),)
    list_display = ("username", "email", "is_staff", "is_active")
