import re
import os
import csv
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from datetime import time, timedelta, date, datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import Seminar, Registration, Attendee


logger = logging.getLogger(__name__)
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

NORTH_ADDRESS='''
<p>Francis Tuttle Technology Center - The Purple Room<br>
12777 N Rockwell Ave<br>
Oklahoma City, OK 73142<br>
Use the Northwest Hall Entrance - (Follow The Purple Signs)<br></p>
'''

SOUTH_ADDRESS='''
<p>Moore Norman Technology Center<br>
13301 S. Pennsylvania Ave,<br>
Oklahoma City, OK 73170<br>
(Follow The Purple Signs)<br></p>'''


def _registrations_for_seminar(seminar):
    return (
        Registration.objects
        .filter(seminar=seminar)
        .select_related("attendee")
        .order_by("attendee__last_name", "attendee__first_name")
    )


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
    html_message = f"""
    <p>Thank you for registering for:<br></p>

    <p><b>{seminar.title}{' : ' if seminar.subtitle != '' else ''}{seminar.subtitle}</b><br></p>

    <p><strong>{seminar.date.strftime("%A").upper()}</strong>, {seminar.date.strftime("%B")} {seminar.date.day} @ {seminar.time.strftime("%I:%M %p")} 
    (Doors open at {(datetime.combine(date.today(), seminar.time) - timedelta(minutes=30)).time().strftime("%I:%M %p")})<br></p>

    {NORTH_ADDRESS if seminar.location =='north' else SOUTH_ADDRESS}

    <p>P.S. We know things can happen, so if you have registered and then can't make it after all, <strong>please call or text us at 405.452.0758</strong> and we will update your registration. Similarly, if you plan to bring a friend, send us a note or call to let us know who to expect!<br></p>

    <p>We look forward to seeing you soon!</p>
    """


    try:
        send_mail(
            subject=subject,
            message="",
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
    except BaseException as e:  
        logger = logging.getLogger(__name__)
        logger.error(f"Email failed: {e}")


def export_sign_in_sheet_csv(seminar):
    registrations = _registrations_for_seminar(seminar)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="sign_in_{seminar.date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["First Name", "Last Name", "Check In"])

    for reg in registrations:
        writer.writerow([
            reg.attendee.first_name,
            reg.attendee.last_name,
            "",  # intentionally blank
        ])

    return response

def export_nametags_csv(seminar, include_header=False):
    registrations = _registrations_for_seminar(seminar)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="nametags_{seminar.date}.csv"'
    )

    writer = csv.writer(response)

    if include_header:
        writer.writerow(["Name"])

    for reg in registrations:
        writer.writerow([
            f"{reg.attendee.first_name} {reg.attendee.last_name}"
        ])

    return response



def get_or_create_attendee(first_name, last_name, email, phone, address, city, zip_code, heard_from):
    candidates = Attendee.objects.none()
    if email != "":
        candidates = Attendee.objects.filter(email=email)
    if phone:
        candidates = candidates or Attendee.objects.filter(phone=phone)
    attendee = candidates.filter(first_name__iexact=first_name).first()
    if not attendee:
        attendee = Attendee.objects.create(
            first_name=first_name.title(),
            last_name=last_name.title(),
            email=email,
            phone=phone,
            address=address,
            city=city,
            zip_code=zip_code,
            heard_from=heard_from
        )
    return attendee


def get_or_create_spouse(first_name, last_name, email, phone, address, city, zip_code, heard_from, attendee):
    spouse_first = first_name.strip().title()
    spouse_last = last_name.strip().title()
    spouse = Attendee.objects.filter(first_name__iexact=spouse_first, last_name__iexact=spouse_last).first()
    if not spouse:
        # create new if no match
        spouse = Attendee.objects.create(
            first_name=spouse_first,
            last_name=spouse_last,
            email=email,
            phone=phone,
            address=address,
            city=city,
            zip_code=zip_code,
            heard_from=heard_from
        )
        
    # Remove old spouse links if either attendee is married
    if attendee.married_to:
        old = attendee.married_to
        old.married_to = None
        old.save()

    if spouse.married_to:
        old = spouse.married_to
        old.married_to = None
        old.save()

    spouse.married_to = attendee
    spouse.save()

    return spouse