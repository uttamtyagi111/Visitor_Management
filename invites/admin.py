from django.contrib import admin
from .models import Invite, InviteStatusTimeline


class InviteStatusTimelineInline(admin.TabularInline):  
    model = InviteStatusTimeline
    extra = 0
    readonly_fields = ("status", "updated_by", "timestamp")  # only show, not edit
    ordering = ("-timestamp",)


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
        "created_at",
    )
    list_filter = ("status", "visit_time", "created_at")
    search_fields = ("visitor_name", "visitor_email", "visitor_phone")
    ordering = ("-created_at",)
    autocomplete_fields = ["invited_by"]

    inlines = [InviteStatusTimelineInline]  # ✅ Show timeline inline inside Invite


@admin.register(InviteStatusTimeline)
class InviteStatusTimelineAdmin(admin.ModelAdmin):
    list_display = ("invite", "status", "updated_by", "timestamp")
    search_fields = (
        "invite__visitor_name",
        "invite__visitor_email",
        "status",
    )
    list_filter = ("status", "timestamp")
    ordering = ("-timestamp",)
    autocomplete_fields = ["invite", "updated_by"]
