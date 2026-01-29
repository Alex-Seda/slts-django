import re
import os
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import Seminar


logger = logging.getLogger(__name__)
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None

    # keep digits only
    digits = re.sub(r"\D", "", phone)

    # handle leading country code
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]

    # basic sanity check
    if len(digits) != 10:
        return None  # or raise ValidationError if you prefer

    return digits


def send_confirmation_email(email, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    subject = f"Registration Confirmation - Senior Living Truth Series"
    message = f"Thank you for registering for {seminar.title}!\n\n"

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
    except BaseException as e:  
        logger = logging.getLogger(__name__)
        logger.error(f"Email failed: {e}")


