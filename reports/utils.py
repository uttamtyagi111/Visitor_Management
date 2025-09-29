from .models import Report
from django.utils import timezone

def add_to_report_from_visitor(visitor):
    report, created = Report.objects.get_or_create(
        visitor=visitor,
        defaults={
            "check_in": timezone.now(),
            
        },
    )

    if not created:
        # report.increment_visit()
        report.check_in = timezone.now()
        report.save(update_fields=["check_in", "visit_count"])

    return report



def add_to_report_from_invite(invite):
    if invite.status == "checked_in":
        report, created = Report.objects.get_or_create(
            invite=invite,
            defaults={
                "check_in": timezone.now(),
                # "visit_count": 1,
            },
        )

        if not created:
            # report.increment_visit()
            report.check_in = timezone.now()  # update last check-in time
            report.save(update_fields=["check_in", "visit_count"])

        return report
# def add_visitor_to_report(visitor):
#     Report.objects.create(
#         visitor=visitor,
#         check_in=timezone.now()
#     )
