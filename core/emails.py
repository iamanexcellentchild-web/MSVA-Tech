import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import close_old_connections
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _run(func, *args):
    """Run func now (tests) or in a background thread, so a slow mail service never delays the visitor."""
    if not settings.EMAIL_ASYNC:
        return func(*args)

    def target():
        try:
            func(*args)
        finally:
            close_old_connections()

    threading.Thread(target=target, daemon=True).start()
    return None


def _send(subject, to, text_template, html_template, context, reply_to=None):
    message = EmailMultiAlternatives(
        subject=subject,
        body=render_to_string(text_template, context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        reply_to=reply_to or [settings.ACADEMY["email"]],
    )
    message.attach_alternative(render_to_string(html_template, context), "text/html")
    message.send(fail_silently=False)


def _application_confirmation(application_id, context):
    from .models import Application

    application = Application.objects.select_related("track").get(pk=application_id)
    context = {**context, "application": application}
    try:
        _send(
            f"Application received: {application.track.title} | {settings.ACADEMY['name']}",
            [application.email], "emails/application_received.txt", "emails/application_received.html", context,
        )
    except Exception:  # mail problems must never break the applicant's submission
        logger.exception("Failed to send application confirmation to %s", application.email)
        return False
    Application.objects.filter(pk=application_id).update(confirmation_email_sent=True)
    return True


def send_application_confirmation(application, request=None):
    """Email the applicant: received, under review, contacted if shortlisted. Never raises."""
    context = {
        "academy": settings.ACADEMY,
        "dashboard_url": request.build_absolute_uri("/dashboard/") if request else "",
        "track_url": request.build_absolute_uri(application.track.get_absolute_url()) if request else "",
    }
    return _run(_application_confirmation, application.pk, context)


def _contact_notification(message_id, admin_url):
    from .models import ContactMessage

    msg = ContactMessage.objects.get(pk=message_id)
    try:
        _send(
            f"[Website contact] {msg.subject}",
            [settings.CONTACT_INBOX], "emails/contact_message.txt", "emails/contact_message.html",
            {"msg": msg, "academy": settings.ACADEMY, "admin_url": admin_url},
            reply_to=[f"{msg.name} <{msg.email}>"],  # hitting Reply answers the visitor directly
        )
    except Exception:
        logger.exception("Failed to forward contact message %s", message_id)
        return False
    return True


def send_contact_notification(message, request=None):
    """Forward a contact-form message to the academy inbox. Never raises."""
    admin_url = request.build_absolute_uri(f"/admin/core/contactmessage/{message.pk}/change/") if request else ""
    return _run(_contact_notification, message.pk, admin_url)
