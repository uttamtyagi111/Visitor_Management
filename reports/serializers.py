from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    visitor_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ["id", "visitor_name", "check_in", "check_out", "remarks", "visit_count"]

    def get_visitor_name(self, obj):
        if obj.invite:
            return obj.invite.visitor_name
        if obj.visitor:
            return obj.visitor.name
        return None
