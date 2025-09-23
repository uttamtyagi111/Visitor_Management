from django.contrib import admin
from .models import QRCode


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "text",
        "created_by",
        "size",
        "error_correction",
        "background",
        "foreground",
        "logo",
        "created_at",
    )
    search_fields = ("text", "created_by__username", "logo")
    list_filter = ("error_correction", "created_at", "created_by")
    readonly_fields = ("created_at",)

    # Optional: display a preview of QR image
    def qr_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100"/>'
        return "-"
    qr_image_preview.allow_tags = True
    qr_image_preview.short_description = "QR Image Preview"
