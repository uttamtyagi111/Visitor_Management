from .models import Report


def add_to_report_from_visitor(visitor):
    report, created = Report.objects.get_or_create(
        name=visitor.name,
        email=visitor.email,
        defaults={"visitor": visitor, "check_in": visitor.created_at},
    )
    if not created:
        report.total_visits += 1
        report.save()


def add_to_report_from_invite(invite):
    report, created = Report.objects.get_or_create(
        name=invite.visitor_name,
        email=invite.visitor_email,
        defaults={"invite": invite, "check_in": invite.created_at},
    )
    if not created:
        report.total_visits += 1
        report.save()
