from rest_framework import serializers
from .models import Visitor, VisitorStatusTimeline


class VisitorSerializer(serializers.ModelSerializer):
    timelines = serializers.SerializerMethodField()
    image = serializers.ImageField(write_only=True, required=False) 

    class Meta:
        model = Visitor
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "purpose",
            "image",
            "created_at",
            "issued_by",
            "status",
            "check_in",
            "check_out",
            "is_active",
            "timelines",
        ]
        read_only_fields = ["created_at", "check_in", "check_out", "is_active", "timelines"]

    def get_timelines(self, obj):
        timelines = obj.status_timelines.all()
        return VisitorStatusTimelineSerializer(timelines, many=True).data


class VisitorStatusTimelineSerializer(serializers.ModelSerializer):
    updated_by = serializers.StringRelatedField()

    class Meta:
        model = VisitorStatusTimeline
        fields = ["id", "status", "updated_by", "timestamp"]
