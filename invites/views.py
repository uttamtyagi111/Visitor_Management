from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone

from reports.utils import add_to_report_from_invite
from .models import Invite
from .serializers import InviteSerializer
import uuid

class InviteListCreateView(generics.ListCreateAPIView):
    queryset = Invite.objects.all().order_by("-created_at")
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        invite = serializer.save(invited_by=self.request.user, invite_code=uuid.uuid4())
        add_to_report_from_invite(invite)

class InviteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"


class InviteDetailByCodeView(generics.RetrieveAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = []  # ❌ No login required for users
    lookup_field = "invite_code"

# ✅ Unified status update instead of 3 separate views
class UpdateInviteStatusView(generics.UpdateAPIView):
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        invite = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(Invite._meta.get_field("status").choices):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        invite.status = new_status
        invite.save()
        return Response(InviteSerializer(invite).data, status=status.HTTP_200_OK)


class VerifyInviteView(APIView):
    """
    Verify invite by invite_code and check if not expired.
    """
    def post(self, request, *args, **kwargs):
        code = request.data.get("invite_code")
        try:
            invite = Invite.objects.get(invite_code=code)
        except Invite.DoesNotExist:
            return Response({"error": "Invalid invite code"}, status=status.HTTP_404_NOT_FOUND)

        # Check expiry
        if invite.expiry_time and invite.expiry_time < timezone.now():
            return Response({"error": "Invite expired"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(InviteSerializer(invite).data, status=status.HTTP_200_OK)

from utils.upload_to_s3 import upload_to_s3

class CaptureVisitorDataView(APIView):
    """
    Capture visitor's image, upload to S3, update status to 'pending',
    and generate a QR code if not already created.
    """
    def post(self, request, *args, **kwargs):
        code = request.data.get("invite_code")
        try:
            invite = Invite.objects.get(invite_code=code)
        except Invite.DoesNotExist:
            return Response({"error": "Invalid invite code"}, status=status.HTTP_404_NOT_FOUND)

        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Image is required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Upload to S3
        filename = f"invites_images/{invite.invite_code}.png"
        image_url = upload_to_s3(image_file, filename)

        # ✅ Save image URL + update status
        invite.image = image_url
        invite.status = "pending"
        invite.save(update_fields=["image", "status"])

        # ✅ Generate QR code (uploads to S3 too)
        invite.generate_qr()

        return Response(
            {"message": "Visitor data captured", "invite": InviteSerializer(invite).data},
            status=status.HTTP_200_OK
        )
