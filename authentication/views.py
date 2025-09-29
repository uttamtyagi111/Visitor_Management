from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.conf import settings
from .serializers import (
    RegisterSerializer, 
    OTPVerifySerializer, 
    UserSerializer, 
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)
from .models import PasswordResetToken
from utils.upload_to_s3 import upload_to_s3

User = get_user_model()

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.create_temp_user(serializer.validated_data)

        # send OTP via email
        send_mail(
            subject="Verify your email",
            message=f"Your OTP is {otp}. It will expire in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[serializer.validated_data['email']],
        )

        return Response(
            {"message": "OTP sent to your email. Please verify to complete registration."},
            status=status.HTTP_200_OK
        )


class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "Email verified successfully. You can now login.", "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=400
            )

        # ✅ Check if user exists
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "No active user with this email exists"},
                status=404
            )

        # ✅ Authenticate with password
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"error": "Email or password is incorrect"},
                status=401
            )

        # ✅ Successful login
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": getattr(user, "role", None),
            }
        }, status=200)



class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        # Build a plain dict to avoid deep-copying uploaded file objects
        data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)

        avatar_file = request.FILES.get("avatar")
        if avatar_file:
            # Validate content type (JPG/PNG)
            allowed_types = ["image/png", "image/jpeg", "image/jpg"]
            if getattr(avatar_file, "content_type", None) not in allowed_types:
                return Response({"error": "Invalid file type. Only PNG, JPG, and JPEG are allowed."}, status=400)

            # Validate size (<= 5MB)
            max_size_bytes = 5 * 1024 * 1024
            if hasattr(avatar_file, "size") and avatar_file.size > max_size_bytes:
                return Response({"error": "File too large. Maximum size is 5MB."}, status=400)

            # Upload to S3
            filename = f"user_avatars/{user.id}_{avatar_file.name}"
            avatar_url = upload_to_s3(avatar_file, filename)
            data["avatar"] = avatar_url

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=205)
        except Exception:
            return Response({"error": "Invalid token"}, status=400)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        token_obj = PasswordResetToken.objects.create(user=user)
        reset_link = f"{settings.FRONTEND_URL}/password-verify/?token={token_obj.token}"

        send_mail(
            subject="Password Reset Request",
            message=f"Click the link to reset your password: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "Password reset link sent to email."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
