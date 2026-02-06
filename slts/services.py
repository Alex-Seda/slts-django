import re
import os
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from datetime import time, timedelta, date, datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import Seminar


logger = logging.getLogger(__name__)
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

NORTH_ADDRESS='''Francis Tuttle Technology Center - The Purple Room
12777 N Rockwell Ave
Oklahoma City, OK 73142
Use the Northwest Hall Entrance - (Follow The Purple Signs)'''

SOUTH_ADDRESS='''Moore Norman Technology Center
13301 S. Pennsylvania Ave,
Oklahoma City, OK 73170
(Follow The Purple Signs)'''


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
    subject = "Senior Living Truth Series Confirmation - " + seminar.date.strftime("%B") + " " + str(seminar.date.year)
    message = f"""Thank you for registering for:

<b>{seminar.title}{' : ' if seminar.subtitle != '' else ''}{seminar.subtitle}</b>

<strong>{seminar.date.strftime("%A").upper()}</strong>, {seminar.date.strftime("%B")} {seminar.date.day} @ {seminar.time.strftime("%I:%M %p")} (Doors open at {(datetime.combine(date.today(), seminar.time) - timedelta(minutes=30)).time().strftime("%I:%M %p")})

{NORTH_ADDRESS if seminar.location =='north' else SOUTH_ADDRESS}

P.S. We know things can happen, so if you have registered and then can't make it after all, <strong>please call or text us at 405.452.0758</strong> and we will update your registration. Similarly, if you plan to bring a friend, send us a note or call to let us know who to expect!

We look forward to seeing you soon!
"""


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


