import re
import os
import csv
import json
import logging
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.http import HttpResponse
from datetime import time, timedelta, date, datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import Seminar, OtherEvent, Registration, Attendee


logger = logging.getLogger(__name__)
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")


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


def send_confirmation_email(email, event_id, event_type):
    if(event_type == 'seminar'):
        event = get_object_or_404(Seminar, id=event_id)
        location = event.location_fk
        location_name = location.full_name
        address = location.address
        city = location.city
        state = location.state
        zip_code = location.zip_code
    else:
        event = get_object_or_404(OtherEvent, id=event_id)
        location_name = None
        address = event.address
        city = event.city
        state = event.state
        zip_code = event.zip_code

    subtitle = getattr(event, "subtitle", None)

    subject = "Senior Living Truth Series Confirmation - " + event.date.strftime("%B") + " " + str(event.date.year)

    html_message = f"""
    <p>Thank you for registering for:<br></p>

    <p><b>{event.title}{f' : {subtitle}' if subtitle else ''}</b><br></p>

    <p><strong>{event.date.strftime("%A").upper()}</strong>, {event.date.strftime("%B")} {event.date.day} @ {event.time.strftime("%I:%M %p")}
    {f'(Doors open at {(datetime.combine(date.today(), event.time) - timedelta(minutes=30)).time().strftime("%I:%M %p")})<br>' if event_type == 'seminar' else ''}</p>

    <p>{f'{location_name}<br>' if location_name else ''}
    {address},<br>
    {city}, {state} {zip_code}<br>
    (Follow The Purple Signs)<br></p>'''

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
        f'attachment; filename="sign_in_{seminar.title.replace(" ", "-")}_{seminar.date}.csv"'
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
        f'attachment; filename="nametags_{seminar.title.replace(" ", "-")}_{seminar.date}.csv"'
    )

    writer = csv.writer(response)

    if include_header:
        writer.writerow(["Name"])

    for reg in registrations:
        writer.writerow([
            f"{reg.attendee.first_name} {reg.attendee.last_name}"
        ])

    return response

def export_attendees_raw_csv(seminar):
    registrations = _registrations_for_seminar(seminar)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="attendee_dump_{seminar.title.replace(" ", "-")}_{seminar.date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["First Name", "Last Name", "Married To", "Address", "City", "State",
                     "Zip Code", "Phone", "Email", "Heard From", "Local", "Notes"])

    for reg in registrations:
        writer.writerow([
            reg.attendee.first_name,
            reg.attendee.last_name,
            f"{reg.attendee.married_to.first_name if reg.attendee.married_to else ''} {reg.attendee.married_to.last_name if reg.attendee.married_to else ''}",
            reg.attendee.address,
            reg.attendee.city,
            reg.attendee.state,
            reg.attendee.zip_code,
            reg.attendee.phone,
            reg.attendee.email,
            f"{reg.attendee.heard_from if reg.attendee.heard_from else ''}",
            reg.attendee.local,
            f"{reg.attendee.notes if reg.attendee.notes else ''}",
        ])

    return response


def get_or_create_attendee(first_name, last_name, email, phone, address, city, zip_code, heard_from, birthday):
    candidates = Attendee.objects.none()
    if email != "":
        candidates = Attendee.objects.filter(email=email)
    if phone:
        candidates = candidates or Attendee.objects.filter(phone=phone)
    attendee = candidates.filter(first_name__iexact=first_name,last_name__iexact=last_name).first()
    if not attendee:
        attendee = Attendee.objects.create(
            first_name=first_name.strip().title(),
            last_name=last_name.strip().title(),
            email=email,
            phone=phone,
            address=address,
            city=city,
            zip_code=zip_code,
            heard_from=heard_from,
            birthday=birthday,
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


def check_api_key(request):
    key = request.headers.get("X-API-Key", "")
    return secrets.compare_digest(key, os.environ.get("N8N_API_KEY"))

def check_registration_info(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return False, "invalid or missing request body"

    sem_date = data.get("seminar-date", "").strip()
    att_first_name = data.get("attendee-first-name", "").strip()
    att_last_name = data.get("attendee-last-name", "").strip()

    def is_valid_name(name):
        return bool(name) and all(c.isalpha() or c in " -'" for c in name)

    if not is_valid_name(att_first_name):
        return False, "invalid or missing attendee-first-name"
    if not is_valid_name(att_last_name):
        return False, "invalid or missing attendee-last-name"

    try:
        datetime.strptime(sem_date, "%Y-%m-%d")
    except ValueError:
        return False, "seminar-date must be in YYYY-MM-DD format"

    return True, None
