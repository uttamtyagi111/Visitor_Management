import qrcode
import os
from io import BytesIO
from django.core.files import File
from django.db import models
from authentication.models import User
from employee.models import Employee


class Invite(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="invites")
    visitor_name = models.CharField(max_length=100)
    visitor_email = models.EmailField()
    visitor_phone = models.CharField(max_length=15, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    invite_date = models.DateTimeField(auto_now_add=True)
    visit_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("checked_in", "Checked In"),
            ("checked_out", "Checked Out"),
            ("rejected", "Rejected")
        ],
        default="pending"
    )
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invite for {self.visitor_name} by {self.employee.user.name}"

    def save(self, *args, **kwargs):
        # Save the object first so we get the ID
        super().save(*args, **kwargs)

        if not self.qr_code:
            qr_data = f"INVITE_ID:{self.id}|Visitor:{self.visitor_name}|Email:{self.visitor_email}|Visit:{self.visit_time}"
            qr_img = qrcode.make(qr_data)

            # Save image in memory
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            file_name = f"invite_{self.id}_qr.png"

            # Save to ImageField
            self.qr_code.save(file_name, File(buffer), save=False)

            buffer.close()
            super().save(update_fields=['qr_code'])
