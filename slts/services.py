import re
import os
import logging
from django.conf import settings
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
        send_email(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=[email],
        )
    except SMTPException as e:  
        logger = logging.getLogger(__name__)
        logger.error(f"Email failed: {e}")


def send_email(subject, message, from_email, to_emails):
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    mail = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        plain_text_content=message
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mail)
        logger.info(f"Email sent: {response.status_code}")
    except Exception as e:
        logger.error(f"SendGrid API error: {e}")


def test_email():
    message = Mail(
        from_email='from_email@example.com',
        to_emails='to@example.com',
        subject='Sending with Twilio SendGrid is Fun',
        html_content='<strong>and easy to do anywhere, even with Python</strong>')
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        # sg.set_sendgrid_data_residency("eu")
        # uncomment the above line if you are sending mail using a regional EU subuser
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
