from rest_framework import serializers
from .models import Invite


class InviteSerializer(serializers.ModelSerializer):
    invited_by = serializers.CharField(source="invited_by.username", read_only=True)

    class Meta:
        model = Invite
        fields = [
            "id",
            "invited_by",
            "visitor_name",
            "visitor_email",
            "visitor_phone",
            "purpose",
            "visit_time",
            "status",
            "qr_code",
            "created_at"
        ]
        read_only_fields = ["id", "status", "qr_code", "created_at", "invited_by"]
        
    def create(self, validated_data):
        # Assign logged-in user as the inviter
        validated_data['invited_by'] = self.context['request'].user
        return super().create(validated_data)