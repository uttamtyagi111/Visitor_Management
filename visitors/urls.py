from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    VisitorListCreateAPIView,
    VisitorDetailAPIView,
    VisitorStatusUpdateAPIView,
    VisitorTimelineAPIView,
    VisitorListWithFiltersAPIView,
)

urlpatterns = [
    path("visitors/", VisitorListCreateAPIView.as_view(), name="visitor-list-create"),
    path("visitors/search/", VisitorListWithFiltersAPIView.as_view(), name="visitor-search"),
    path("visitors/<int:pk>/", VisitorDetailAPIView.as_view(), name="visitor-detail"),
    path("visitors/<int:pk>/status/", VisitorStatusUpdateAPIView.as_view(), name="visitor-status"),
    path("visitors/<int:pk>/timeline/", VisitorTimelineAPIView.as_view(), name="visitor-timeline"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
