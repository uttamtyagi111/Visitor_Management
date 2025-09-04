from django.db import models
from invites.models import Invite
from visitors.models import Visitor

class Report(models.Model):
    invite = models.OneToOneField(
        Invite, on_delete=models.CASCADE, null=True, blank=True, related_name="report"
    )
    visitor = models.OneToOneField(
        Visitor, on_delete=models.CASCADE, null=True, blank=True, related_name="report"
    )
    check_in = models.DateTimeField(blank=True, null=True)
    check_out = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    visit_count = models.PositiveIntegerField(default=1)  # ✅ Track visits

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["invite"], condition=models.Q(invite__isnull=False), name="unique_invite_report"
            ),
            models.UniqueConstraint(
                fields=["visitor"], condition=models.Q(visitor__isnull=False), name="unique_visitor_report"
            ),
        ]

    def increment_visit(self):
        """Increase count instead of duplicating report"""
        self.visit_count += 1
        self.save(update_fields=["visit_count"])

    def __str__(self):
        if self.invite:
            return f"Report for {self.invite.visitor_name} (visits: {self.visit_count})"
        elif self.visitor:
            return f"Report for {self.visitor.name} (visits: {self.visit_count})"
        return "Unknown Report"
