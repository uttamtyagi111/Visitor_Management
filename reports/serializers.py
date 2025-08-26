from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    visitor_name = serializers.CharField(source="invite.visitor_name", read_only=True)
    employee_name = serializers.CharField(source="invite.employee.user.name", read_only=True)

    class Meta:
        model = Report
        fields = ["id", "visitor_name", "employee_name", "check_in_time", "check_out_time", "remarks"]
