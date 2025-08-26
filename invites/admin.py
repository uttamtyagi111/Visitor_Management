from django.contrib import admin
from .models import Invite


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "employee", 
        "visitor_name", 
        "visitor_email", 
        "visit_time", 
        "status", 
        "created_at"
    )
    list_filter = ("status", "invite_date", "visit_time")
    search_fields = ("visitor_name", "visitor_email", "visitor_phone")
    ordering = ("-created_at",)
