from django.db import models
from authentication.models import User
from invites.models import Invite

class Report(models.Model):
    invite = models.OneToOneField(Invite, on_delete=models.CASCADE, related_name="report")
    check_in = models.DateTimeField(blank=True, null=True)
    check_out = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Report for {self.invite.visitor_name}"
