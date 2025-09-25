from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.timezone import now
import django_filters
from .models import Visitor, VisitorStatusTimeline
from .serializers import VisitorSerializer, VisitorStatusTimelineSerializer
from utils.upload_to_s3 import upload_to_s3
from reports.utils import add_to_report_from_visitor
from visitors.utils import send_visitor_status_email


@api_view(['POST'])
@permission_classes([AllowAny])  # Anyone can register
def create_visitor(request):
    """
    Create or update a visitor based on email.
    - New visitor: Creates a new record with status 'pending' (image = None initially)
    - Returning visitor: Updates phone/purpose, keeps name, marks status 'revisit'
    """
    try:
        email = request.data.get('email', '').strip()
        name = request.data.get('name', '').strip()
        phone = request.data.get('phone', '').strip()
        purpose = request.data.get('purpose', '').strip()

        # ✅ Validate required fields
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if visitor exists by email
        visitor = Visitor.objects.filter(email=email).first()

        if visitor:
            # --------------------------
            # Returning visitor
            # --------------------------
            visitor.phone = phone  # Update phone
            if purpose:
                visitor.purpose = purpose  # Update purpose if provided
            visitor.status = "revisit"  # ✅ Mark as revisit
            visitor.save()

            # ✅ Add timeline entry
            VisitorStatusTimeline.objects.create(
                visitor=visitor,
                status=visitor.status,
                updated_by=None
            )

            # ✅ Increment visit_count in Report
            add_to_report_from_visitor(visitor)
            send_visitor_status_email(visitor)

            return Response({
                'id': visitor.id,
                'name': visitor.name,
                'email': visitor.email,
                'phone': visitor.phone,
                'purpose': visitor.purpose,
                'status': visitor.status,
                'image': visitor.image,  # may be existing
                'visit_count': visitor.report.visit_count if hasattr(visitor, "report") else 1,
                'message': 'Returning visitor recorded as revisit.'
            }, status=status.HTTP_200_OK)

        else:
            # --------------------------
            # New visitor (image = None for now)
            # --------------------------
            visitor = Visitor.objects.create(
                name=name,
                email=email,
                phone=phone,
                purpose=purpose,
                status='created',
                image=None
            )

            # ✅ Add initial timeline
            VisitorStatusTimeline.objects.create(
                visitor=visitor,
                status=visitor.status,
                updated_by=None
            )

            # ✅ Create report record
            add_to_report_from_visitor(visitor)
            send_visitor_status_email(visitor)

            return Response({
                'id': visitor.id,
                'name': visitor.name,
                'email': visitor.email,
                'phone': visitor.phone,
                'purpose': visitor.purpose,
                'status': visitor.status,
                'image': visitor.image,  # will be null
                'visit_count': 1,
                'message': 'New visitor registered successfully (image pending upload).'
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_qr_info(request):
    """Get information for QR code display"""
    return Response({
        'registration_url': f"{request.build_absolute_uri('/')[:-1]}/visitor",
        'title': 'Visitor Registration',
        'description': 'Scan to register as a visitor',
        'instructions': 'Please scan this QR code with your phone to start the visitor registration process.'
    })

class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all().select_related("issued_by")
    serializer_class = VisitorSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]  # Anyone can submit visitor form
        return [IsAuthenticated()]  # Only staff can view visitors
    
    def perform_create(self, serializer):
        image_file = self.request.FILES.get("image")
        if image_file:
            filename = f"visitor_images/{image_file.name}"
            image_url = upload_to_s3(image_file, filename)
            visitor = serializer.save(image=image_url)
            print("Image uploaded to S3:", image_url)
        else:
            visitor = serializer.save()
            print("No image uploaded.")
            
        add_to_report_from_visitor(visitor)
        send_visitor_status_email(visitor)

class VisitorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Visitor.objects.all().select_related("issued_by")
    serializer_class = VisitorSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        if request.method != "PATCH":
            return Response(
                {"error": "Only PATCH method is allowed for updates."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        partial = True
        instance = self.get_object()
        
        # ✅ Capture old status BEFORE updating
        old_status = instance.status  

        # --- Handle Visitor Image Upload ---
        image_file = request.FILES.get("image")
        if image_file:
            filename = f"visitor_images/{instance.id}_{image_file.name}"
            image_url = upload_to_s3(image_file, filename)

            request.data._mutable = True
            request.data["image"] = image_url
            request.data["status"] = "pending"  # ✅ FIX: Put status in request.data
            request.data._mutable = False
            
            # ❌ REMOVE: Don't set instance.status here
            # instance.status = "pending"  

        # --- Handle Visitor Pass File Upload ---
        pass_file = request.FILES.get("pass_file")
        if pass_file:
            allowed_types = ["image/png", "image/jpeg", "image/jpg"]
            if pass_file.content_type not in allowed_types:
                return Response(
                    {"error": "Invalid file type. Only PNG, JPG, and JPEG are allowed."},
                    status=400
                )

            filename = f"visitor_passes/{instance.id}_{pass_file.name}"
            pass_file_url = upload_to_s3(pass_file, filename)

            request.data._mutable = True
            request.data["pass_file"] = pass_file_url
            request.data._mutable = False

        # --- Save the updated data ---
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()  # ✅ FIX: Get the saved instance

        # ✅ FIX: Use the saved instance status
        final_status = updated_instance.status
        
        # ✅ Track status change with correct status
        if final_status != old_status:
            VisitorStatusTimeline.objects.create(
                visitor=updated_instance,  # ✅ Use updated instance
                status=final_status,       # ✅ Use final status
                updated_by=request.user if request.user.is_authenticated else None
            )
            print(f"✅ Timeline created: {old_status} → {final_status}")

        # ✅ Update report
        add_to_report_from_visitor(updated_instance)

        return Response(serializer.data)




class VisitorStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        visitor = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(Visitor.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Update status and timestamps
        visitor.status = new_status
        if new_status == "checked_in":
            visitor.check_in = now()
        elif new_status == "checked_out":
            visitor.check_out = now()
            visitor.is_active = False
        visitor.save()

        # ✅ Log status timeline
        VisitorStatusTimeline.objects.create(
            visitor=visitor, status=new_status, updated_by=request.user
        )

        # ✅ Send status email
        # if checked_in -> attach the pass file (from S3/local)
        pass_file = None
        if new_status == "checked_in" and visitor.pass_file:
            # Download file from S3 using requests
            import requests
            response = requests.get(visitor.pass_file)
            if response.status_code == 200:
                from django.core.files.base import ContentFile
                file_content = ContentFile(response.content)
                file_content.name = visitor.pass_file.split("/")[-1]
                pass_file = file_content

        send_visitor_status_email(visitor, pass_file=pass_file)

        return Response(VisitorSerializer(visitor).data)



# ---------------------------
# Visitor Status Timeline
# ---------------------------
class VisitorTimelineAPIView(generics.ListAPIView):
    serializer_class = VisitorStatusTimelineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        visitor_id = self.kwargs["pk"]
        return VisitorStatusTimeline.objects.filter(visitor_id=visitor_id)


# ---------------------------
# Visitor List with Filters
# ---------------------------
class VisitorFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    phone = django_filters.CharFilter(field_name="phone", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    issued_by = django_filters.NumberFilter(field_name="issued_by__id")
    created_at = django_filters.DateFromToRangeFilter(field_name="created_at")
    check_in = django_filters.DateFromToRangeFilter(field_name="check_in")
    check_out = django_filters.DateFromToRangeFilter(field_name="check_out")

    class Meta:
        model = Visitor
        fields = ["id", "status", "issued_by", "is_active"]


class VisitorListWithFiltersAPIView(generics.ListAPIView):
    queryset = Visitor.objects.select_related("issued_by").all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = VisitorFilter
    search_fields = ["name", "email", "phone", "purpose"]
    ordering_fields = ["id", "status", "check_in", "check_out", "created_at", "name"]
    ordering = ["-id"]

