from rest_framework import viewsets, permissions
from .models import Report
from .serializers import ReportSerializer

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('visitor', 'invite').all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
 