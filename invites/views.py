import qrcode
import os
from django.conf import settings
from django.core.files import File
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Invite
from .serializers import InviteSerializer


class InviteListCreateView(generics.ListCreateAPIView):
    queryset = Invite.objects.all().order_by("-created_at")
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        invite = serializer.save()
        
        # ✅ Generate QR Code with invite details
        qr_data = f"InviteID:{invite.id} | Visitor:{invite.visitor_name} | Email:{invite.visitor_email} | Time:{invite.visit_time}"
        qr_img = qrcode.make(qr_data)

        # Save path
        qr_dir = os.path.join(settings.MEDIA_ROOT, "qr_codes")
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = os.path.join(qr_dir, f"invite_{invite.id}.png")

        qr_img.save(qr_path)

        # Attach to model
        with open(qr_path, "rb") as f:
            invite.qr_code.save(f"invite_{invite.id}.png", File(f), save=True)


class InviteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]


class ApproveInviteView(generics.UpdateAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        invite = self.get_object()
        invite.status = "approved"
        invite.save()
        return Response(InviteSerializer(invite).data, status=status.HTTP_200_OK)


class CheckInView(generics.UpdateAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        invite = self.get_object()
        invite.status = "checked_in"
        invite.save()
        return Response(InviteSerializer(invite).data, status=status.HTTP_200_OK)


class CheckOutView(generics.UpdateAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        invite = self.get_object()
        invite.status = "checked_out"
        invite.save()
        return Response(InviteSerializer(invite).data, status=status.HTTP_200_OK)
