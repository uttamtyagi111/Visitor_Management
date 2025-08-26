from django.contrib import admin
from .models import Visitor, VisitorPass

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "company", "id_proof", "id_number", "created_at")
    search_fields = ("name", "email", "phone", "company")


@admin.register(VisitorPass)
class VisitorPassAdmin(admin.ModelAdmin):
    list_display = ("visitor", "issued_by", "purpose", "check_in", "check_out", "is_active")
    search_fields = ("visitor__name", "purpose")
    list_filter = ("is_active", "check_in", "check_out")
