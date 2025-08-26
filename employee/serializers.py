from rest_framework import serializers
from .models import Employee
from authentication.serializers import UserSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'email', 'name', 'designation', 'department', 'phone', "is_active", "created_at","updated_at"]
    read_only_fields = ['id', 'email', 'name', "created_at", "updated_at"]