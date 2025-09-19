from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    visitor_data = serializers.SerializerMethodField()
    invite_data = serializers.SerializerMethodField()
    visitor_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "visitor_name", "check_in", "check_out", "remarks", 
            "visit_count", "visitor_data", "invite_data", "image"
        ]

    def get_visitor_data(self, obj):
        if obj.visitor:
            return {
                "name": obj.visitor.name,
                "email": obj.visitor.email,
                "phone": obj.visitor.phone,
                "purpose": obj.visitor.purpose,
                "status": obj.visitor.status,
                "image": obj.visitor.image
            }
        return None

    def get_invite_data(self, obj):
        if obj.invite:
            return {
                "visitor_name": obj.invite.visitor_name,
                "visitor_email": obj.invite.visitor_email,
                "visitor_phone": obj.invite.visitor_phone,
                "purpose": obj.invite.purpose,
                "status": obj.invite.status,
                "image": obj.invite.image
            }
        return None

    def get_visitor_name(self, obj):
        if obj.visitor:
            return obj.visitor.name
        if obj.invite:
            return obj.invite.visitor_name
        return "Unknown"

    def get_image(self, obj):
        if obj.image:
            return obj.image
        if obj.visitor and obj.visitor.image:
            return obj.visitor.image
        if obj.invite and obj.invite.image:
            return obj.invite.image
        return None