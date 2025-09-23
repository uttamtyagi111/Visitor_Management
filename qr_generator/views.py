from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

from .models import QRCode
from .serializers import QRCodeSerializer
from utils.upload_to_s3 import upload_to_s3


class QRCodeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QRCodeSerializer

    def get_queryset(self):
        # Return only QR codes created by the logged-in user
        return QRCode.objects.filter(created_by=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        request = self.request
        default_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/visitor"
        data = request.data.get("data", default_url)

        size = int(request.data.get("size", 256))
        error_correction = request.data.get("error_correction", "M")
        background = request.data.get("background", "#ffffff")
        foreground = request.data.get("foreground", "#000000")

        # Map error correction
        error_map = {
            "L": ERROR_CORRECT_L,
            "M": ERROR_CORRECT_M,
            "Q": ERROR_CORRECT_Q,
            "H": ERROR_CORRECT_H,
        }
        error_level = error_map.get(error_correction.upper(), ERROR_CORRECT_M)

        # Generate QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_level,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=foreground, back_color=background).convert("RGB")

        # Handle logo upload
        # logo_file = request.FILES.get("logo")
        # logo_url = None
        # if logo_file:
        #     logo = Image.open(logo_file)
        #     qr_width, qr_height = img.size
        #     logo_size = qr_width // 4
        #     logo.thumbnail((logo_size, logo_size))
        #     xpos = (qr_width - logo.width) // 2
        #     ypos = (qr_height - logo.height) // 2
        #     img.paste(logo, (xpos, ypos), mask=logo if logo.mode == "RGBA" else None)

        #     # Upload logo to S3 and get URL
        #     logo_file.seek(0)
        #     logo_url = upload_to_s3(logo_file, f"qr_logos/{logo_file.name}")

        # Resize QR
        img = img.resize((size, size))

        # Save QR to memory buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_content = ContentFile(buffer.getvalue(), name="qr.png")

        # Save instance
        serializer.save(
            text=data,
            image=qr_content,
            # logo=logo_url,
            size=size,
            error_correction=error_correction,
            background=background,
            foreground=foreground,
            created_by=request.user,
        )
