from rest_framework import serializers
from .models import Invite, InviteStatusTimeline

class InviteStatusTimelineSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField()

    class Meta:
        model = InviteStatusTimeline
        fields = ["id", "status", "updated_by", "timestamp"]
class InviteSerializer(serializers.ModelSerializer):
    invited_by = serializers.CharField(source="invited_by.username", read_only=True)
    timelines = serializers.SerializerMethodField()
    class Meta:
        model = Invite
        fields = [
            "id", "invited_by",
            "visitor_name", "visitor_email", "visitor_phone", "purpose",
            "visit_time", "expiry_time",   # ✅ keep visit timings
            "invite_code",                 # ✅ unique invite code
            "image",                       # ✅ uploaded image
            "status", "qr_code", "pass_image",         # ✅ QR code + status+ pass_image
            "created_at",# ✅ created timestamp
            "timelines",                   # ✅ status timelines
        ]
        read_only_fields = [
            "id", "status", "qr_code", "pass_image", "created_at",
            "invited_by", "invite_code", "timelines",
        ]

    def get_timelines(self, obj):
        timelines = obj.status_timelines.all()
        return InviteStatusTimelineSerializer(timelines, many=True).data