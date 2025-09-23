from rest_framework import serializers
from .models import QRCode

class QRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRCode
        fields = "__all__"
        read_only_fields = ["logo", "image", "created_by", "created_at"]
