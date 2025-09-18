from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.timezone import now
import django_filters
from .models import Visitor, VisitorStatusTimeline
from .serializers import VisitorSerializer, VisitorStatusTimelineSerializer
from utils.upload_to_s3 import upload_to_s3
from reports.utils import add_to_report_from_visitor
# ---------------------------
# Visitor CRUD + Pass Handling
# ---------------------------

# s3_client = boto3.client(
#     "s3",
#     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#     region_name=settings.AWS_S3_REGION_NAME,
# )

# def upload_to_s3(file_obj, filename):
#     """
#     Uploads a file object to S3 and returns the URL.
#     """
#     bucket_name = settings.AWS_STORAGE_BUCKET_NAME
#     s3_client.upload_fileobj(file_obj, bucket_name, filename, ExtraArgs={'ACL': 'public-read'})
#     url = f"https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{filename}"
#     return url

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from .models import Visitor
from .serializers import VisitorSerializer

@api_view(['POST'])
@permission_classes([AllowAny])  # No authentication required for visitor registration
def create_visitor(request):
    """Create a new visitor registration"""
    try:
        # Extract data from request
        visitor_data = {
            'name': request.data.get('name', '').strip(),
            'phone': request.data.get('phone', '').strip(),
            'email': request.data.get('email', '').strip(),
            'purpose': request.data.get('purpose', ''),
            'status': 'pending',  # Always starts as pending
        }
        
        # Validate required fields
        if not visitor_data['name']:
            return Response({
                'error': 'Name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not visitor_data['phone']:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if image is provided (required)
        if 'image' not in request.FILES:
            return Response({
                'error': 'Image is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # Basic image validation
        if not image_file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            return Response({
                'error': 'Only JPG, JPEG, and PNG files are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create visitor
        visitor = Visitor.objects.create(**visitor_data)
        
        # Upload image to S3
        filename = f"visitor_images/{visitor.id}_{image_file.name}"
        image_url = upload_to_s3(image_file, filename)
        
        if not image_url:
            # Delete visitor if image upload fails
            visitor.delete()
            return Response({
                'error': 'Image upload failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update visitor with image URL
        visitor.image = image_url
        visitor.save()
        
        VisitorStatusTimeline.objects.create(
            visitor=visitor,
            status=visitor.status,
            updated_by=None  # no user since it’s self-registration
        )
        
        add_to_report_from_visitor(visitor)
        
        return Response({
            'id': visitor.id,
            'name': visitor.name,
            'phone': visitor.phone,
            'email': visitor.email,
            'status': visitor.status,
            'image': visitor.image,
            'created_at': visitor.created_at,
            'message': 'Visitor registered successfully. Please wait for approval.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class VisitorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Visitor.objects.all().select_related("issued_by")
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # ✅ Capture old status BEFORE updating
        old_status = instance.status  

        image_file = request.FILES.get("image")
        if image_file:
            filename = f"visitor_images/{image_file.name}"
            image_url = upload_to_s3(image_file, filename)
            request.data._mutable = True  # allow editing request.data
            request.data["image"] = image_url
            request.data._mutable = False

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # ✅ Compare new status with old
        if instance.status != old_status:
            VisitorStatusTimeline.objects.create(
                visitor=instance, status=instance.status, updated_by=request.user
            )

        # ✅ update report after edit
        add_to_report_from_visitor(instance)

        return Response(serializer.data)



# ---------------------------
# Update Visitor Status (check-in, check-out, approve, reject)
# ---------------------------
class VisitorStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        visitor = self.get_object()
        new_status = request.data.get("status")
        print(f"Updating visitor {visitor.id} status to {new_status}")
        if new_status not in dict(Visitor.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        visitor.status = new_status
        if new_status == "checked_in":
            visitor.check_in = now()
        elif new_status == "checked_out":
            visitor.check_out = now()
            visitor.is_active = False
        visitor.save() 

        # log timeline
        VisitorStatusTimeline.objects.create(
            visitor=visitor, status=new_status, updated_by=request.user
        )

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

