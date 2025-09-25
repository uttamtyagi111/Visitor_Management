import uuid
from django.utils import timezone
import qrcode
from io import BytesIO
from django.db import models
from django.conf import settings
from utils.upload_to_s3 import upload_to_s3
from django.contrib.auth import get_user_model

User = get_user_model()


class Invite(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("reinvited", "Reinvited"),
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
        ("rejected", "Rejected"),
    ]

    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invites")
    visitor_name = models.CharField(max_length=100)
    visitor_email = models.EmailField(unique=True)
    visitor_phone = models.CharField(max_length=15, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    visit_time = models.DateTimeField()
    expiry_time = models.DateTimeField(null=True, blank=True)
    checked_out = models.DateTimeField(null=True, blank=True)
    invite_code = models.CharField(max_length=6, unique=True, editable=False,null=True, blank=True)
    image = models.URLField(blank=True, null=True)   # ✅ S3 image URL
    qr_code = models.URLField(blank=True, null=True)
    pass_image = models.URLField(blank=True, null=True)  # ✅ S3 pass image URL

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.visitor_name} ({self.visitor_email}) - status: {self.status}"

    def generate_qr(self):
        """
        Generate QR code only if visitor image exists and QR not generated yet.
        Upload QR code to S3 and save its URL.
        """
        if self.image and not self.qr_code:
            qr_data = {
                "invite_code": str(self.invite_code),
                "visitor_name": self.visitor_name,
                "visitor_email": self.visitor_email,
                "visitor_phone": self.visitor_phone,
                "purpose": self.purpose,
                "visit_time": str(self.visit_time),
                "image": self.image,
            }

            qr_img = qrcode.make(str(qr_data))
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            buffer.seek(0)

            qr_filename = f"qr_codes/invite_{self.invite_code}.png"
            qr_url = upload_to_s3(buffer, qr_filename)

            self.qr_code = qr_url
            self.save(update_fields=["qr_code"])


class InviteStatusTimeline(models.Model):
    invite = models.ForeignKey("Invite", on_delete=models.CASCADE, related_name="status_timelines")
    status = models.CharField(max_length=20, choices=Invite.STATUS_CHOICES)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.invite.visitor_name} - {self.status} @ {self.timestamp}"
