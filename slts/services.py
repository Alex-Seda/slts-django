from django.core import signing
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from urllib.parse import quote, unquote
from .models import Seminar, RegistrationToken


# Registration token logic for 
def generate_registration_token(email, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return RegistrationToken.objects.create(
        email=email,
        seminar=seminar,
    )

def parse_registration_token(token, max_age=60*60*24*3):
    try:
        # print("Token after: ", repr(token))
        signed = force_str(urlsafe_base64_decode(token))
        # print("Signed data after: ", repr(signed))
        data = signing.loads(signed, max_age=max_age)
        # print("Raw data after: " + repr(data))
        return data["email"], data["seminar_id"]
    except Exception:
        raise ValueError("Invalid or expired token")


# Email functionality
def send_completion_email(email, seminar_id):
    token_obj = generate_registration_token(email, seminar_id)
    # print("Token object: ", repr(token_obj))
    # print("Token: ", repr(token_obj.token))

    link = f"{settings.SITE_URL}/complete-registration/{token_obj.token}/"

    subject = "Complete Your Seminar Registration"  
    message = (
        f"Thank you for your interest in the Senior Living Truth Series!\n\n"
        f"Click the link below to finish your registration:\n\n"
        f"{link}\n\n"
        "This link will expire in 3 days."
    )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

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




