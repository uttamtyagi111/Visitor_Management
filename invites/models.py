import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.conf import settings
from utils.upload_to_s3 import upload_to_s3  # your existing S3 upload function
from django.contrib.auth import get_user_model
User = get_user_model()

class Invite(models.Model):
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invites")
    visitor_name = models.CharField(max_length=100)
    visitor_email = models.EmailField()
    visitor_phone = models.CharField(max_length=15, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    visit_time = models.DateTimeField()
    expiry_time = models.DateTimeField(null=True, blank=True)

    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    image = models.URLField(blank=True, null=True)   # ✅ S3 image URL
    qr_code = models.URLField(blank=True, null=True)  # ✅ S3 QR code URL

    status = models.CharField(
        max_length=20,
        choices=[
            ("created", "Created"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("checked_in", "Checked In"),
            ("checked_out", "Checked Out"),
            ("rejected", "Rejected"),
        ],
        default="created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.visitor_name} ({self.status})"

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

            # generate QR image
            qr_img = qrcode.make(str(qr_data))
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            buffer.seek(0)

            qr_filename = f"qr_codes/invite_{self.invite_code}.png"
            qr_url = upload_to_s3(buffer, qr_filename)

            self.qr_code = qr_url
            self.save(update_fields=["qr_code"])
