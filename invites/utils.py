from django.core.mail import EmailMessage, send_mail
from django.conf import settings
import mimetypes
import requests
from django.core.files.base import ContentFile



def build_invite_link(request, invite_code: str) -> str:
    """Build the invite verification link."""
    frontend_base = getattr(settings, "FRONTEND_URL", None)
    path = f"/invite/{invite_code}/"
    if frontend_base:
        return frontend_base.rstrip("/") + path
    base = request.build_absolute_uri("/").rstrip("/")
    return base + path


def send_invite_email(invite, request):
    if not invite.visitor_email:
        return False

    subject, message = "", ""

    if invite.status in ["created", "reinvited"]:   #  initial invite or revisit
        subject = "You're invited to Wish Geeks Techserve"
        link = build_invite_link(request, invite.invite_code)
        message = (
            f"Dear {invite.visitor_name},\n\n"
            "You are being invited to Wish Geeks Techserve.\n\n"
            f"Your invite code is: {invite.invite_code}.\n\n"
            "To proceed, complete your verification using the link below.\n"
            "You will need to capture your live image and submit the form.\n\n"
            f"Verification link: {link}\n\n"
            "Regards,\nVisitor Management Team"
        )

    elif invite.status == "pending":
        subject = "Invite Pending Verification"
        message = f"Dear {invite.visitor_name},\n\nYour invite is pending verification.\n\nRegards,\nVisitor Management Team"

    elif invite.status == "approved":
        subject = "Invite Approved"
        message = f"Dear {invite.visitor_name},\n\nYour invite has been approved.\n\nRegards,\nVisitor Management Team"

    elif invite.status == "rejected":
        subject = "Invite Rejected"
        message = f"Dear {invite.visitor_name},\n\nUnfortunately, your invite has been rejected.\n\nRegards,\nVisitor Management Team"

    elif invite.status == "checked_in":
        subject = "Invite Checked In - Pass Attached"
        message = f"Dear {invite.visitor_name},\n\nYou have successfully checked in. Your pass is attached.\n\nRegards,\nVisitor Management Team"

    elif invite.status == "checked_out":
        subject = "Invite Checked Out"
        message = f"Dear {invite.visitor_name},\n\nYou have successfully checked out. Thank you for visiting.\n\nRegards,\nVisitor Management Team"

    try:
        if invite.status == "checked_in" and invite.pass_image:
            response = requests.get(invite.pass_image)
            if response.status_code == 200:
                file_content = ContentFile(response.content)
                file_content.name = invite.pass_image.split("/")[-1]
                content_type, _ = mimetypes.guess_type(file_content.name)
                if not content_type:
                    content_type = "application/octet-stream"

                email = EmailMessage(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [invite.visitor_email],
                )
                email.attach(file_content.name, file_content.read(), content_type)
                email.send(fail_silently=False)
        else:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [invite.visitor_email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Failed to send invite email to {invite.visitor_email}: {e}")
        return False
