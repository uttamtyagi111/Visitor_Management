from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Visitor(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    id_proof = models.CharField(max_length=100, blank=True, null=True)  # e.g., Aadhaar, Passport
    id_number = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class VisitorPass(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="passes")
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    purpose = models.CharField(max_length=255)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Pass for {self.visitor.name} - {'Active' if self.is_active else 'Closed'}"
