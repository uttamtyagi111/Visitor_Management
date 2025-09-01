from django.contrib import admin
from .models import Visitor, VisitorStatusTimeline


class VisitorStatusTimelineInline(admin.TabularInline):  
    model = VisitorStatusTimeline
    extra = 0
    readonly_fields = ("status", "updated_by", "timestamp")
    ordering = ("-timestamp",)


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "purpose",
        "status",      # ✅ pass status now inside Visitor
        "issued_by",
        "check_in",
        "check_out",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "email", "phone", "purpose")
    list_filter = ("status", "is_active", "created_at", "check_in", "check_out")
    ordering = ("-created_at",)
    autocomplete_fields = ["issued_by"]

    inlines = [VisitorStatusTimelineInline]  # ✅ show timeline inside Visitor


@admin.register(VisitorStatusTimeline)
class VisitorStatusTimelineAdmin(admin.ModelAdmin):
    list_display = ("visitor", "status", "updated_by", "timestamp")
    search_fields = (
        "visitor__name",
        "visitor__email",
        "status",
    )
    list_filter = ("status", "timestamp")
    ordering = ("-timestamp",)
    autocomplete_fields = ["visitor", "updated_by"]
