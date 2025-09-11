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
from . import views
urlpatterns = [
    path('visitor/', views.create_visitor, name='create-visitor'),
    
    # QR code info endpoint (optional)
    path('qr/info/', views.get_qr_info, name='qr-info'),
    path("visitors/", VisitorListCreateAPIView.as_view(), name="visitor-list-create"),
    path("visitors/search/", VisitorListWithFiltersAPIView.as_view(), name="visitor-search"),
    path("visitors/<int:pk>/", VisitorDetailAPIView.as_view(), name="visitor-detail"),
    path("visitors/<int:pk>/status/", VisitorStatusUpdateAPIView.as_view(), name="visitor-status"),
    path("visitors/<int:pk>/timeline/", VisitorTimelineAPIView.as_view(), name="visitor-timeline"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
