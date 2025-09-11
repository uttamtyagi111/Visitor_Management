from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Visitor(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
        ("rejected", "Rejected"),
    ]

    # Basic visitor details
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    purpose = models.CharField(max_length=255, null=False, blank=False)
    image = models.URLField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    # Pass related fields (merged from VisitorPass)
    issued_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="issued_passes"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    check_in = models.DateTimeField(blank=True, null=True)
    check_out = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.email}) - Status: {self.status}"


class VisitorStatusTimeline(models.Model):
    """Keeps track of status updates for a visitor's pass"""

    visitor = models.ForeignKey(
        Visitor, on_delete=models.CASCADE, related_name="status_timelines"
    )
    status = models.CharField(max_length=20, choices=Visitor.STATUS_CHOICES)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.visitor.name} - {self.status} @ {self.timestamp}"
# from django.db import models
# from django.contrib.auth import get_user_model
# from django.utils import timezone

# User = get_user_model()


# class Visitor(models.Model):
#     STATUS_CHOICES = [
#         ("pending", "Pending"),
#         ("approved", "Approved"),
#         ("checked_in", "Checked In"),
#         ("checked_out", "Checked Out"),
#         ("rejected", "Rejected"),
#     ]
#     PURPOSE_CHOICES = [
#         ('business_meeting', 'Business Meeting'),
#         ('interview', 'Interview'),
#         ('delivery', 'Delivery'),
#         ('maintenance', 'Maintenance'),
#         ('personal', 'Personal Visit'),
#         ('other', 'Other'),
#     ]

#     # Basic visitor details
#     name = models.CharField(max_length=255)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20)
#     purpose = models.CharField(max_length=255,choices=PURPOSE_CHOICES, null=False, blank=False)
#     image = models.URLField(blank=True, null=True) 
#     created_at = models.DateTimeField(auto_now_add=True)

#     # Pass related fields (merged from VisitorPass)
#     issued_by = models.ForeignKey(
#         User, on_delete=models.SET_NULL, null=True, blank=True, related_name="issued_passes"
#     )
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
#     check_in = models.DateTimeField(blank=True, null=True)
#     check_out = models.DateTimeField(blank=True, null=True)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return f"{self.name} ({self.email}) - Status: {self.status}"


# class VisitorStatusTimeline(models.Model):
#     """Keeps track of status updates for a visitor's pass"""

#     visitor = models.ForeignKey(
#         Visitor, on_delete=models.CASCADE, related_name="status_timelines"
#     )
#     status = models.CharField(max_length=20, choices=Visitor.STATUS_CHOICES)
#     updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     timestamp = models.DateTimeField(default=timezone.now)

#     class Meta:
#         ordering = ["-timestamp"]

#     def __str__(self):
#         return f"{self.visitor.name} - {self.status} @ {self.timestamp}"
