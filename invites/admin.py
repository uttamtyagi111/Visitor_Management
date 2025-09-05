from django.contrib import admin
from .models import Invite


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "visitor_name", 
        "visitor_email", 
        "invite_code", 
        "invited_by",
        "visit_time", 
        "status", 
        "created_at"
    )
    list_filter = ("status", "visit_time")
    search_fields = ("visitor_name", "visitor_email", "visitor_phone")
    ordering = ("-created_at",)
