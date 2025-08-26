from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("invite", "check_in", "check_out", "remarks")
    search_fields = ("invite__visitor_name", "remarks")
    list_filter = ("check_in", "check_out")
