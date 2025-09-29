from rest_framework import serializers
from .models import Invite, InviteStatusTimeline
from reports.serializers import ReportSerializer

class InviteStatusTimelineSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField()

    class Meta:
        model = InviteStatusTimeline
        fields = ["id", "status", "updated_by", "timestamp"]

class InviteSerializer(serializers.ModelSerializer):
    invited_by = serializers.CharField(source="invited_by.username", read_only=True)
    timelines = serializers.SerializerMethodField()
    report = ReportSerializer(read_only=True)  # Include report info (check_in/check_out)
    
    class Meta:
        model = Invite
        fields = [
            "id",
            "invited_by",
            "visitor_name",
            "visitor_email",
            "visitor_phone",
            "purpose",
            "visit_time",      # Scheduled visit time (frontend shows this)
            "expiry_time",
            "checked_out",     # Actual checked_out from Invite
            "invite_code",
            "image",
            "status",
            "qr_code",
            "pass_image",
            "created_at",
            "timelines",
            "report",          # Include actual check-in/check-out from Report
        ]
        read_only_fields = [
            "id",
            "status",
            "qr_code",
            "pass_image",
            "created_at",
            "invited_by",
            "invite_code",
            "timelines",
            "report",
        ]

    def get_timelines(self, obj):
        timelines = obj.status_timelines.all()
        return InviteStatusTimelineSerializer(timelines, many=True).data
