from django.db import models
from django.conf import settings

class QRCode(models.Model):
    text = models.TextField()  # QR Code text/URL
    image = models.ImageField(upload_to="qr_codes/")  # QR code image
    logo = models.URLField(null=True, blank=True)  # URL of uploaded logo
    size = models.IntegerField(default=256)
    error_correction = models.CharField(max_length=2, default="M")
    background = models.CharField(max_length=7, default="#ffffff")
    foreground = models.CharField(max_length=7, default="#000000")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="qr_codes"
    )

    def __str__(self):
        return f"QR for {self.text[:50]}"
