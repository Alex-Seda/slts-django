from django.core.signing import TimestampSigner
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings


# Registration token logic for 
signer = TimestampSigner()

def generate_registration_token(email, seminar_id):
    # Raw value
    value = f"{email}|{seminar_id}"
    # Sign it
    signed_value = signer.sign(value)
    # Encode URL-safe
    token = urlsafe_base64_encode(force_bytes(signed_value))
    return token

def parse_registration_token(token, max_age=60*60*24*3):
    try:
        # Decode first
        signed_value = force_str(urlsafe_base64_decode(token))
        # Unsign
        value = signer.unsign(signed_value, max_age=max_age)
        email, seminar_id = value.split("|")
        return email, int(seminar_id)
    except Exception:
        raise ValueError("Invalid or expired token")


# Email functionality
def send_completion_email(email, seminar_id):
    token = generate_registration_token(email, seminar_id)
    link = f"{settings.SITE_URL}/complete-registration/?token={token}"
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





