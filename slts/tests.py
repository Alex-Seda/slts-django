from datetime import date, time

from django.core import mail
from django.test import TestCase, override_settings

from slts.models import Location, Seminar
from slts.services import send_confirmation_email


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.com",
)
class SendConfirmationEmailTests(TestCase):
    def test_send_confirmation_email_for_seminar(self):
        location = Location.objects.create(
            name="North Campus",
            full_name="North Campus (Francis Tuttle)",
            series="north",
            address="123 Main St",
            city="Edmond",
            state="OK",
            zip_code="73003",
            color="purple",
        )
        seminar = Seminar.objects.create(
            title="Estate Planning Essentials",
            subtitle="What Families Should Know",
            description="",
            date=date(2026, 10, 15),
            time=time(10, 0),
            location="north",
            location_fk=location,
            status="scheduled",
        )

        send_confirmation_email("test@example.com", seminar.id, "seminar")

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["test@example.com"])
        self.assertEqual(message.from_email, "noreply@example.com")
        self.assertIn("Senior Living Truth Series Confirmation", message.subject)
        self.assertEqual(message.body, "")
        self.assertTrue(message.alternatives)
        self.assertIn("Estate Planning Essentials", message.alternatives[0][0])
