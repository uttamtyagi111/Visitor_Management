from rest_framework import serializers
from .models import Visitor, VisitorPass

class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = "__all__"


class VisitorPassSerializer(serializers.ModelSerializer):
    visitor = VisitorSerializer(read_only=True)
    visitor_id = serializers.PrimaryKeyRelatedField(
        queryset=Visitor.objects.all(), source="visitor", write_only=True
    )

    class Meta:
        model = VisitorPass
        fields = ["id", "visitor", "visitor_id", "issued_by", "purpose", "check_in", "check_out", "is_active"]
        read_only_fields = ["check_in", "check_out", "is_active"]
