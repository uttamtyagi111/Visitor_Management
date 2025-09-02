from rest_framework import serializers
from .models import Invite


class InviteSerializer(serializers.ModelSerializer):
    invited_by = serializers.CharField(source="invited_by.username", read_only=True)

    class Meta:
        model = Invite
        fields = [
            "id", "invited_by",
            "visitor_name", "visitor_email", "visitor_phone", "purpose",
            "visit_time", "expiry_time",   # ✅ keep visit timings
            "invite_code",                 # ✅ unique invite code
            "image",                       # ✅ uploaded image
            "status", "qr_code",           # ✅ QR code + status
            "created_at",                  # ✅ created timestamp
        ]
        read_only_fields = [
            "id", "status", "qr_code", "created_at",
            "invited_by", "invite_code"
        ]

