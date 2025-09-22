from django.core.mail import send_mail
from django.conf import settings
import logging


def build_invite_link(request, invite_code: str) -> str:
    """
    Build the invite verification link, preferring FRONTEND_URL if available.
    Falls back to request.build_absolute_uri.
    """
    frontend_base = getattr(settings, "FRONTEND_URL", None)
    path = f"/invite/{invite_code}/"
    if frontend_base:
        return frontend_base.rstrip("/") + path
    # fallback to current host
    base = request.build_absolute_uri("/").rstrip("/")
    return base + path


def send_invite_email(invite, request) -> bool:
    """
    Send an invitation email to the visitor with their invite code and link.
    """
    recipient = getattr(invite, "visitor_email", None)
    if not recipient:
        return False

    link = build_invite_link(request, invite.invite_code)

    subject = "You're invited to Wish Geeks Techserve"
    message = (
        f"Dear {invite.visitor_name},\n\n"
        "You are being invited to Wish Geeks Techserve.\n\n"
        f"Your invite code is: {invite.invite_code}.\n\n"
        "To proceed, complete your verification using the link below.\n"
        "You will need to capture your live image and submit the form.\n\n"
        f"Verification link: {link}\n\n"
        "Regards,\nVisitor Management Team"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost")

    try:
        send_mail(
            subject,
            message,
            from_email,
            [recipient],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logging.getLogger(__name__).exception(
            "Failed to send invite email to %s with code %s", recipient, invite.invite_code
        )
        return False


