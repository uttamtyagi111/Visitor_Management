from django.urls import path
from .views import (
    VisitorListCreateAPIView,
    VisitorDetailAPIView,
    VisitorPassCreateAPIView,
    VisitorPassCheckoutAPIView,
)

urlpatterns = [
    path("visitors/", VisitorListCreateAPIView.as_view(), name="visitor-list-create"),
    path("visitors/<int:pk>/", VisitorDetailAPIView.as_view(), name="visitor-detail"),
    path("visitor-passes/", VisitorPassCreateAPIView.as_view(), name="visitor-pass-create"),
    path("visitor-passes/<int:pk>/checkout/", VisitorPassCheckoutAPIView.as_view(), name="visitor-pass-checkout"),
]
