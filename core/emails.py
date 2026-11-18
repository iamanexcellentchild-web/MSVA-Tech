import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_application_confirmation(application, request=None):
    """Email the applicant a confirmation. Returns True on success; never raises."""
    context = {
        "application": application,
        "academy": settings.ACADEMY,
        "dashboard_url": request.build_absolute_uri("/dashboard/") if request else "",
        "track_url": request.build_absolute_uri(application.track.get_absolute_url()) if request else "",
    }
    subject = f"Application received: {application.track.title} | {settings.ACADEMY['name']}"
    text_body = render_to_string("emails/application_received.txt", context)
    html_body = render_to_string("emails/application_received.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[application.email],
        reply_to=[settings.ACADEMY["email"]],
    )
    message.attach_alternative(html_body, "text/html")
    try:
        message.send(fail_silently=False)
    except Exception:  # SMTP errors shouldn't break the applicant's submission
        logger.exception("Failed to send application confirmation to %s", application.email)
        return False

    application.confirmation_email_sent = True
    application.save(update_fields=["confirmation_email_sent"])
    return True
