from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone

from reports.utils import add_to_report_from_invite
from .models import Invite, InviteStatusTimeline
from .serializers import InviteSerializer
import uuid

class InviteListCreateView(generics.ListCreateAPIView):
    queryset = Invite.objects.all().order_by("-created_at")
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        short_code = str(uuid.uuid4()).replace("-", "")[:6]  # ✅ 6 chars
        invite = serializer.save(invited_by=self.request.user, invite_code=short_code)
        # Log initial status in timeline
        InviteStatusTimeline.objects.create(
            invite=invite, status=invite.status, updated_by=self.request.user
        )
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
        data = request.data
        status_updated = False
        details_updated = False

        # 1️⃣ Check if status is being updated
        new_status = data.get("status")
        if new_status:
            if new_status not in dict(Invite._meta.get_field("status").choices):
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            
            if new_status != invite.status:
                invite.status = new_status
                invite.save(update_fields=["status"])
                status_updated = True

                # Timeline for status change
                InviteStatusTimeline.objects.create(
                    invite=invite,
                    status=new_status,
                    updated_by=request.user
                )

        # 2️⃣ Check if other fields are updated
        editable_fields = ["visitor_name", "visitor_email", "visitor_phone", "purpose", "visit_time", "expiry_time", "image", "pass_image"]
        changes = []
        for field in editable_fields:
            if field in data and getattr(invite, field) != data[field]:
                changes.append(field)
                setattr(invite, field, data[field])
        
        if changes:
            invite.save(update_fields=changes)
            details_updated = True

            # Timeline for details change
            InviteStatusTimeline.objects.create(
                invite=invite,
                status=f"Details updated ({', '.join(changes)})",
                updated_by=request.user
            )

        # 3️⃣ Optional: existing report function
        add_to_report_from_invite(invite)

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
        
        InviteStatusTimeline.objects.create(
            invite=invite, status="pending", updated_by=None
        )
        # add_to_report_from_invite(invite)

        # # ✅ Generate QR code (uploads to S3 too)
        # invite.generate_pass_and_qr()

        return Response(
            {"message": "Visitor data captured", "invite": InviteSerializer(invite).data},
            status=status.HTTP_200_OK
        )
# views.py
# from django.http import HttpResponseRedirect

# class ServePassView(generics.RetrieveAPIView):
#     queryset = Invite.objects.all()
#     serializer_class = InviteSerializer
#     permission_classes = []  # No login required for scanning
#     lookup_field = "invite_code"

#     def get(self, request, *args, **kwargs):
#         invite = self.get_object()
        
#         # Check expiry
#         if invite.expiry_time and invite.expiry_time < timezone.now():
#             return Response({"error": "Invite expired"}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Redirect to pass_image URL
#         if invite.pass_image:
#             return HttpResponseRedirect(invite.pass_image)
#         return Response({"error": "Pass not generated"}, status=status.HTTP_404_NOT_FOUND)

