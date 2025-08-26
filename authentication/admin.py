from django.contrib import admin
from .models import User, PasswordResetToken

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "role", "phone", "is_active", "is_staff")
    search_fields = ("email", "role", "phone")

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token", "created_at", "expires_at")
    search_fields = ("user__email", "token")
    list_filter = ("created_at", "expires_at")
