from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from reports.utils import add_to_report_from_invite
from .models import Invite
from .serializers import InviteSerializer, InviteStatusTimelineSerializer
from .models import Invite, InviteStatusTimeline
from .utils import send_invite_email
import uuid

class InviteListCreateView(generics.ListCreateAPIView):
    queryset = Invite.objects.all().order_by("-created_at")
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        visitor_email = serializer.validated_data.get("visitor_email")

        # ✅ Check if email already exists in Invite table
        if Invite.objects.filter(visitor_email=visitor_email).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"visitor_email": "An invite with this email already exists."})
        
        short_code = str(uuid.uuid4()).replace("-", "")[:6]  # ✅ 6 chars
        invite = serializer.save(invited_by=self.request.user, invite_code=short_code)
        # add initial timeline entry
        try:
            InviteStatusTimeline.objects.create(
                invite=invite,
                status="created",
                updated_by=self.request.user,
            )
            send_invite_email(invite, self.request)
            print ("Invite email sent successfully.")
            
        except Exception as e:
            print (f"Failed to create invite status timeline: {e}")
            pass
        

class ReinviteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            invite = Invite.objects.get(pk=pk)
        except Invite.DoesNotExist:
            return Response({"detail": "Invite not found."}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Store old purpose for timeline
        old_purpose = invite.purpose

        # ✅ Generate new invite_code
        invite.invite_code = str(uuid.uuid4()).replace("-", "")[:6]
        data = request.data
        # If somehow request.data is not a dict (e.g., int), wrap it
        if not isinstance(data, dict):
            return Response({"detail": "Invalid data format, expected JSON object."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ Get new data from frontend
        visit_time = request.data.get("visit_time")
        expiry_time = request.data.get("expiry_time")
        new_purpose = request.data.get("purpose")

        if not visit_time or not expiry_time:
            return Response(
                {"detail": "visit_time and expiry_time are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Update invite fields
        invite.visit_time = visit_time
        invite.expiry_time = expiry_time
        if new_purpose:
            invite.purpose = new_purpose

        # ✅ Update status
        invite.status = "reinvited"
        invite.save(update_fields=["invite_code", "visit_time", "expiry_time", "purpose", "status"])

        # ✅ Add timeline for reinvite
        InviteStatusTimeline.objects.create(
            invite=invite,
            status="reinvited",
            updated_by=request.user,
            # notes=f"Purpose updated from '{old_purpose}' to '{invite.purpose}'" if new_purpose else None
        )

        # ✅ Send email again
        send_invite_email(invite, request)

        return Response({"detail": "Invite reinvited successfully."}, status=status.HTTP_200_OK)


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

        if invite.status != new_status:
            invite.status = new_status
            invite.save()
        
        InviteStatusTimeline.objects.create(
                invite=invite,
                status=new_status,
                updated_by=request.user
            )
        
        add_to_report_from_invite(invite)
        send_invite_email(invite, request)
        
        
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
        print("Invite verified:", invite.__dict__)
        return Response(InviteSerializer(invite).data, status=status.HTTP_200_OK)

from utils.upload_to_s3 import upload_to_s3

class CaptureinviteDataView(APIView):
    """
    Capture invite's image, upload to S3, update status to 'pending',
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
                invite=invite,
                status="pending",
                updated_by=request.user if request.user.is_authenticated else None
            )
        send_invite_email(invite, request)
        # add_to_report_from_invite(invite)

        # # ✅ Generate QR code (uploads to S3 too)
        # invite.generate_pass_and_qr()

        return Response(
            {"message": "Invites data captured", "invite": InviteSerializer(invite).data},
            status=status.HTTP_200_OK
        )
        
        
        
class InviteTimelineAPIView(generics.ListAPIView):
    serializer_class = InviteStatusTimelineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        invite_id = self.kwargs["pk"]
        return InviteStatusTimeline.objects.filter(invite_id=invite_id)

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
