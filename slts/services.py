from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Seminar
import re



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
    message = (
        f"Thank you for registering for {seminar.title}!\n\n"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )




