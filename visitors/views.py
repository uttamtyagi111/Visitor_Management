from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Visitor, VisitorPass
from .serializers import VisitorSerializer, VisitorPassSerializer
from django.utils.timezone import now


# Visitor CRUD
class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]


class VisitorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]


# Visitor Pass APIs
class VisitorPassCreateAPIView(generics.CreateAPIView):
    queryset = VisitorPass.objects.all()
    serializer_class = VisitorPassSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)


class VisitorPassCheckoutAPIView(generics.UpdateAPIView):
    queryset = VisitorPass.objects.all()
    serializer_class = VisitorPassSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        pass_instance = self.get_object()
        if pass_instance.is_active:
            pass_instance.is_active = False
            pass_instance.check_out = now()
            pass_instance.save()
            return Response(VisitorPassSerializer(pass_instance).data)
        return Response({"detail": "Pass already closed"}, status=status.HTTP_400_BAD_REQUEST)
