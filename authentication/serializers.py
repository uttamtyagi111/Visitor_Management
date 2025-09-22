import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetToken
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from .utils import generate_otp  # your OTP util
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    
    def validate_role(self, value):
        allowed_roles = ["admin", "employee"]  # Only these roles allowed in registration
        if value.lower() not in allowed_roles:
            raise serializers.ValidationError("Role must be either 'admin' or 'employee'.")
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Email already registered."})
        return attrs

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already registered.")
        # Optional: simple regex check for digits only, length 10–15
        if not re.fullmatch(r'\d{10,15}', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value

    def validate_username(self, value):
        # Check if username is alphanumeric and at least 3 characters
        if not value.isalnum() or len(value) < 3:
            raise serializers.ValidationError("Username must be alphanumeric and at least 3 characters long.")
        
        # Check uniqueness in the database
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        
        return value


    def create_temp_user(self, validated_data):
        """Instead of saving user, save temp data + otp in cache"""
        otp = generate_otp()

        cache.set(
            f"register_{validated_data['email']}",
            {
                "username": validated_data["username"],
                "email": validated_data["email"],
                "phone": validated_data["phone"],
                "password": validated_data["password"],
                "otp": otp,
            },
            timeout=300  # OTP valid for 5 minutes
        )

        # TODO: send OTP via email here
        return otp
    
    
class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        temp_data = cache.get(f"register_{data['email']}")
        if not temp_data:
            raise serializers.ValidationError("No registration found or OTP expired.")

        if temp_data["otp"] != data["otp"]:
            raise serializers.ValidationError("Invalid OTP.")

        return data

    def save(self, **kwargs):
        temp_data = cache.get(f"register_{self.validated_data['email']}")
        user = User.objects.create_user(
            username=temp_data["username"],
            email=temp_data["email"],
            phone=temp_data["phone"],
            password=temp_data["password"],
            is_active=True
        )
        cache.delete(f"register_{self.validated_data['email']}")  # cleanup
        return user



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "avatar",
            "company",
            "department",
            "address",
            "bio",
            "date_joined",
        ]
        read_only_fields = ["email", "date_joined"]




class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        try:
            token_obj = PasswordResetToken.objects.get(token=data['token'])
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired token.")

        if token_obj.is_expired():
            raise serializers.ValidationError("Token has expired.")
        return data

    def save(self, **kwargs):
        token_obj = PasswordResetToken.objects.get(token=self.validated_data['token'])
        user = token_obj.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        token_obj.delete()  # delete after use
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data.get("current_password")):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        if data.get("new_password") != data.get("new_password2"):
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        if data.get("current_password") == data.get("new_password"):
            raise serializers.ValidationError({"new_password": "New password must be different from current password."})
        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


