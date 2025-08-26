import qrcode
import io
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Invite

class InviteSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.user.name", read_only=True)

    class Meta:
        model = Invite
        fields = [
            "id",
            "employee",
            "employee_name",
            "visitor_name",
            "visitor_email",
            "visitor_phone",
            "purpose",
            "invite_date",
            "visit_time",
            "status",
            "qr_code",
            "created_at"
        ]
        extra_kwargs = {
            "employee": {"write_only": True}
        }

    def create(self, validated_data):
        # ✅ Create Invite object first
        invite = Invite.objects.create(**validated_data)

        # ✅ Generate QR code content (you can customize)
        qr_content = f"Invite ID: {invite.id}\nVisitor: {invite.visitor_name}\nDate: {invite.invite_date}\nTime: {invite.visit_time}"

        # ✅ Generate QR code image
        qr = qrcode.make(qr_content)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        file_name = f"invite_{invite.id}.png"

        # ✅ Save QR code to model
        invite.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)

        return invite
