from rest_framework import viewsets, permissions
from .permissions import EmployeeRolePermission
from .models import Employee
from .serializers import EmployeeSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated, EmployeeRolePermission]
