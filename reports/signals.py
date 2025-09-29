from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Report
from invites.models import Invite
from visitors.models import Visitor

@receiver(post_save, sender=Invite)
def sync_report_with_invite(sender, instance, created, **kwargs):
    """
    Ensure Report is created or updated whenever an Invite is saved.
    """
    if instance.status == "checked_in":
        report, created = Report.objects.get_or_create(
            invite=instance,
            defaults={
                "check_in": timezone.now(),
                "visit_count": 1,
                "image": instance.image,  # ✅ copy latest image
            },
        )

        if not created:
            # ✅ User already has a report → increment and update check-in
            report.increment_visit()
            report.check_in = timezone.now()
            report.image = instance.image
            report.save(update_fields=["check_in", "visit_count", "image"])

    elif instance.status == "checked_out":
        try:
            report = instance.report  # because of related_name="report"
            report.check_out = timezone.now()
            report.save(update_fields=["check_out"])
        except Report.DoesNotExist:
            pass  # no report yet, ignore
        
        
        



@receiver(post_save, sender=Visitor)
def sync_report_with_visitor(sender, instance, created, **kwargs):
    """
    Ensure Report is created or updated whenever a Visitor is saved.
    """
    if instance.status == "checked_in":
        report, created = Report.objects.get_or_create(
            visitor=instance,
            defaults={
                "check_in": timezone.now(),
                "visit_count": 1,
                "image": instance.image,  # ✅ copy latest image
            },
        )

        if not created:
            # ✅ Existing visitor → increment visits, update check-in
            report.increment_visit()
            print("Visitor already has a report, incrementing visit count.")
            report.check_in = timezone.now()
            report.image = instance.image
            report.save(update_fields=["check_in", "visit_count", "image"])

    elif instance.status == "checked_out":
        try:
            report = instance.report  # because of related_name="report"
            report.check_out = timezone.now()
            report.save(update_fields=["check_out"])
        except Report.DoesNotExist:
            pass  # no report yet, ignore

