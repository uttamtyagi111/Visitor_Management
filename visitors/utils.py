from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
import mimetypes


def send_visitor_status_email(visitor, pass_file=None):
    """
    Send an email to a visitor about their current status.
    Includes frontend-generated pass as attachment when provided.
    """
    if not visitor.email:
        return False  

    subject, message = "", ""

    if visitor.status == "pending":
        subject = "Visitor Registration Pending"
        message = f"Dear {visitor.name},\n\nYour registration is pending approval.\n\nRegards,\nVisitor Management Team"

    elif visitor.status == "approved":
        subject = "Visitor Registration Approved"
        message = f"Dear {visitor.name},\n\nYour registration has been approved. Please visit reception to collect your pass.\n\nRegards,\nVisitor Management Team"

    elif visitor.status == "rejected":
        subject = "Visitor Registration Rejected"
        message = f"Dear {visitor.name},\n\nUnfortunately, your registration has been rejected.\n\nRegards,\nVisitor Management Team"

    elif visitor.status == "checked_in":
        subject = "Visitor Checked In - Pass Attached"
        message = f"Dear {visitor.name},\n\nYou have successfully checked in. Your visitor pass is attached.\n\nRegards,\nVisitor Management Team"

    elif visitor.status == "checked_out":
        subject = "Visitor Checked Out"
        message = f"Dear {visitor.name},\n\nYou have successfully checked out. Thank you for visiting.\n\nRegards,\nVisitor Management Team"

    try:
        if visitor.status == "checked_in" and pass_file:
            content_type, _ = mimetypes.guess_type(pass_file.name)
            if not content_type:
                content_type = "application/octet-stream"  # fallback
            # send with attachment
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [visitor.email],
            )
            email.attach(pass_file.name, pass_file.read(), content_type)
            email.send(fail_silently=False)
        else:
            # send simple email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [visitor.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Failed to send email to {visitor.email}: {e}")
        return False
