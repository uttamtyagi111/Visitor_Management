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

