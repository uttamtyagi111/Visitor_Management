import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from django.conf import settings



class Invite(models.Model):
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name="invites"
    )
    visitor_name = models.CharField(max_length=100)
    visitor_email = models.EmailField()
    visitor_phone = models.CharField(max_length=15, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    visit_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("created", "Created"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("checked_in", "Checked In"),
            ("checked_out", "Checked Out"),
            ("rejected", "Rejected")
        ],
        default="created"
    )
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.visitor_name} ({self.status})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save first so we have an ID

        if not self.qr_code:
            qr_data = (
                f"INVITE_ID:{self.id} | Visitor:{self.visitor_name} | "
                f"Email:{self.visitor_email} | Visit:{self.visit_time}"
            )
            qr_img = qrcode.make(qr_data)

            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            file_name = f"invite_{self.id}.png"
            self.qr_code.save(file_name, File(buffer), save=False)
            buffer.close()

            super().save(update_fields=["qr_code"])
