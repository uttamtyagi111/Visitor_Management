from django.urls import path
from .views import QRCodeListCreateView

urlpatterns = [
    path("qr/codes/", QRCodeListCreateView.as_view(), name="generate-qr"),
]
