import csv
import io
import json
import os
from datetime import date, time
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import AttendeeForm
from .models import (
    Attendee,
    Location,
    OtherEvent,
    Registration,
    Seminar,
)
from .services import (
    check_registration_info,
    export_attendees_raw_csv,
    export_nametags_csv,
    export_sign_in_sheet_csv,
    normalize_phone,
    send_confirmation_email,
)


class TestDataMixin:
    def create_location(self, **kwargs):
        values = {
            "name": "North Campus",
            "full_name": "North Campus (Francis Tuttle)",
            "series": "north",
            "address": "123 Main St",
            "city": "Edmond",
            "state": "OK",
            "zip_code": "73003",
            "color": "purple",
        }
        values.update(kwargs)
        return Location.objects.create(**values)

    def create_seminar(self, **kwargs):
        values = {
            "title": "Estate Planning Essentials",
            "subtitle": "What Families Should Know",
            "description": "Learn the basics.",
            "date": date(2026, 10, 15),
            "time": time(10, 0),
            "location_fk": self.create_location(),
            "status": "scheduled",
        }
        values.update(kwargs)
        return Seminar.objects.create(**values)

    def create_other_event(self, **kwargs):
        values = {
            "title": "Community Tour",
            "event_type": "tour",
            "description": "A guided tour.",
            "date": date(2026, 11, 5),
            "time": time(14, 0),
            "address": "456 Oak Ave",
            "city": "Bethany",
            "state": "OK",
            "zip_code": "73008",
            "status": "scheduled",
        }
        values.update(kwargs)
        return OtherEvent.objects.create(**values)

    def create_attendee(self, **kwargs):
        values = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "address": "1 Main St",
            "city": "Edmond",
            "state": "OK",
            "zip_code": "73003",
            "phone": "405-555-0100",
            "email": "ada@example.com",
            "heard_from": "website",
            "birthday": date(1980, 1, 2),
        }
        values.update(kwargs)
        return Attendee.objects.create(**values)


class AttendeeFormTests(TestCase):
    def valid_data(self, **overrides):
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "address": "1 Main St",
            "city": "Edmond",
            "state": "OK",
            "zip_code": "73003",
            "email": "ada@example.com",
            "phone": "405-555-0100",
            "heard_from": "website",
            "birthday": "1980-01-02",
            "spouse_first_name": "",
        }
        data.update(overrides)
        return data

    def test_accepts_a_single_first_name_and_strips_whitespace(self):
        form = AttendeeForm(self.valid_data(first_name=" Ada "))

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["first_name"], "Ada")

    def test_rejects_compound_first_names(self):
        for first_name in ("Ada and Grace", "Ada & Grace", "Ada, Grace", "Ada/Grace"):
            with self.subTest(first_name=first_name):
                form = AttendeeForm(self.valid_data(first_name=first_name))
                self.assertFalse(form.is_valid())
                self.assertIn("one person's first name only", form.errors["first_name"][0])

    def test_spouse_first_name_is_optional_but_validated(self):
        self.assertTrue(AttendeeForm(self.valid_data()).is_valid())
        form = AttendeeForm(self.valid_data(spouse_first_name="Ada and Grace"))

        self.assertFalse(form.is_valid())
        self.assertIn("one person's first name only", form.errors["spouse_first_name"][0])


class ModelTests(TestDataMixin, TestCase):
    def test_setting_a_spouse_updates_both_sides(self):
        attendee = self.create_attendee()
        spouse = self.create_attendee(
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
        )

        attendee.married_to = spouse
        attendee.save()

        attendee.refresh_from_db()
        spouse.refresh_from_db()
        self.assertEqual(attendee.married_to, spouse)
        self.assertEqual(spouse.married_to, attendee)

    def test_replacing_a_spouse_clears_the_old_relationship(self):
        attendee = self.create_attendee()
        old_spouse = self.create_attendee(first_name="Grace", last_name="Hopper")
        new_spouse = self.create_attendee(first_name="Katherine", last_name="Johnson")
        attendee.married_to = old_spouse
        attendee.save()

        attendee.married_to = new_spouse
        attendee.save()

        old_spouse.refresh_from_db()
        new_spouse.refresh_from_db()
        self.assertIsNone(old_spouse.married_to)
        self.assertEqual(new_spouse.married_to, attendee)

    def test_seminar_querysets_filter_and_order_events(self):
        earlier = self.create_seminar(title="Earlier", date=date(2026, 1, 1))
        self.create_seminar(title="Draft", date=date(2026, 2, 1), status="draft")
        later = self.create_seminar(title="Later", date=date(2026, 12, 1))

        self.assertEqual(Seminar.objects.open_seminars().count(), 2)
        self.assertEqual(list(Seminar.objects.get_seminars_by_year(2026)), [earlier, later])
        self.assertEqual(Seminar.objects.get_next_north_seminar(), earlier)

    def test_other_event_querysets_exclude_drafts(self):
        tour = self.create_other_event()
        self.create_other_event(title="Draft Tour", status="draft")
        expert = self.create_other_event(title="Expert", event_type="exin")

        self.assertEqual(list(OtherEvent.objects.get_tours()), [tour])
        self.assertEqual(list(OtherEvent.objects.get_expert_insights()), [expert])

    def test_youtube_urls_are_converted_to_embed_urls(self):
        seminar = self.create_seminar(url="https://www.youtube.com/watch?v=abcdefghijk")
        self.assertEqual(
            seminar.to_embed_url(),
            "https://www.youtube.com/embed/abcdefghijk",
        )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.com",
)
class ServiceTests(TestDataMixin, TestCase):
    def test_normalize_phone_handles_country_code_and_invalid_values(self):
        self.assertEqual(normalize_phone("(405) 555-0100"), "4055550100")
        self.assertEqual(normalize_phone("+1 405-555-0100"), "4055550100")
        self.assertIsNone(normalize_phone("555-0100"))
        self.assertIsNone(normalize_phone(None))

    def test_check_registration_info_validates_body_and_names(self):
        valid, error = check_registration_info(
            type(
                "Request",
                (),
                {
                    "body": json.dumps(
                        {
                            "seminar-date": "2026-10-15",
                            "attendee-first-name": "Ada",
                            "attendee-last-name": "Lovelace",
                        }
                    ).encode()
                },
            )()
        )
        self.assertTrue(valid)
        self.assertIsNone(error)

        invalid, error = check_registration_info(
            type("Request", (), {"body": b'{"seminar-date": "15-10-2026"}'})()
        )
        self.assertFalse(invalid)
        self.assertEqual(error, "invalid or missing attendee-first-name")

    def test_send_confirmation_email_for_seminar(self):
        seminar = self.create_seminar()

        send_confirmation_email("test@example.com", seminar.id, "seminar")

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["test@example.com"])
        self.assertEqual(message.from_email, "noreply@example.com")
        self.assertIn("Senior Living Truth Series Confirmation", message.subject)
        self.assertIn("Estate Planning Essentials", message.alternatives[0][0])
        self.assertIn("Doors open at", message.alternatives[0][0])

    def test_send_confirmation_email_for_other_event_omits_doors_open(self):
        event = self.create_other_event()

        send_confirmation_email("test@example.com", event.id, "tour")

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("Doors open at", mail.outbox[0].alternatives[0][0])

    def test_csv_exports_are_sorted_and_include_expected_columns(self):
        seminar = self.create_seminar()
        second = self.create_attendee(first_name="Bea", last_name="Smith")
        first = self.create_attendee(first_name="Ada", last_name="Adams")
        Registration.objects.create(seminar=seminar, attendee=second)
        Registration.objects.create(seminar=seminar, attendee=first)

        sign_in = list(csv.reader(io.StringIO(export_sign_in_sheet_csv(seminar).content.decode())))
        nametags = list(csv.reader(io.StringIO(export_nametags_csv(seminar, include_header=True).content.decode())))
        raw = list(csv.reader(io.StringIO(export_attendees_raw_csv(seminar).content.decode())))

        self.assertEqual(sign_in[0], ["First Name", "Last Name", "Check In"])
        self.assertEqual(sign_in[1][:2], ["Ada", "Adams"])
        self.assertEqual(nametags[1:], [["Ada Adams"], ["Bea Smith"]])
        self.assertEqual(raw[0][0:3], ["First Name", "Last Name", "Married To"])
        self.assertEqual(raw[1][0:2], ["Ada", "Adams"])


class ViewTests(TestDataMixin, TestCase):
    def test_schedule_redirects_unknown_event_type(self):
        response = self.client.get(reverse("slts:schedule", args=("unknown", 2026)))

        self.assertRedirects(response, reverse("slts:home"))

    def test_schedule_lists_non_draft_seminars_for_year(self):
        self.create_seminar(title="Scheduled Seminar")
        self.create_seminar(title="Draft Seminar", status="draft")

        response = self.client.get(reverse("slts:schedule", args=("seminars", 2026)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scheduled Seminar")
        self.assertNotContains(response, "Draft Seminar")

    def test_register_redirects_for_non_scheduled_event(self):
        seminar = self.create_seminar(status="completed")

        response = self.client.get(
            reverse("slts:register", args=("seminar", seminar.id))
        )

        self.assertRedirects(response, reverse("slts:home"))

    @patch("slts.views.send_confirmation_email")
    def test_register_submit_creates_attendee_and_registration(self, send_email):
        seminar = self.create_seminar()
        response = self.client.post(
            reverse("slts:register_submit", args=("seminar", seminar.id)),
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "address": "1 Main St",
                "city": "Edmond",
                "state": "OK",
                "zip_code": "73003",
                "email": "ADA@example.com",
                "phone": "(405) 555-0100",
                "heard_from": "website",
                "birthday": "1980-01-02",
                "spouse_first_name": "",
            },
        )

        attendee = Attendee.objects.get()
        self.assertRedirects(
            response,
            reverse("slts:registration_success", args=("seminar", seminar.id)),
        )
        self.assertEqual(attendee.email, "ada@example.com")
        self.assertEqual(str(attendee.phone), "+14055550100")
        self.assertTrue(Registration.objects.filter(seminar=seminar, attendee=attendee).exists())
        send_email.assert_called_once_with("ada@example.com", seminar.id, "seminar")


class ApiRegistrationTests(TestDataMixin, TestCase):
    def setUp(self):
        self.seminar = self.create_seminar()
        self.attendee = self.create_attendee()
        self.url = reverse("slts:api_register_submit")

    def payload(self):
        return {
            "seminar-date": str(self.seminar.date),
            "attendee-first-name": self.attendee.first_name,
            "attendee-last-name": self.attendee.last_name,
        }

    @patch.dict(os.environ, {"N8N_API_KEY": "test-api-key"})
    def test_requires_api_key(self):
        response = self.client.post(self.url, data=json.dumps(self.payload()), content_type="application/json")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    @patch.dict(os.environ, {"N8N_API_KEY": "test-api-key"})
    def test_registers_existing_attendee_with_valid_request(self):
        response = self.client.post(
            self.url,
            data=json.dumps(self.payload()),
            content_type="application/json",
            HTTP_X_API_KEY="test-api-key",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})
        self.assertTrue(
            Registration.objects.filter(
                seminar=self.seminar,
                attendee=self.attendee,
            ).exists()
        )

    @patch.dict(os.environ, {"N8N_API_KEY": "test-api-key"})
    def test_returns_not_found_for_unknown_seminar(self):
        payload = self.payload()
        payload["seminar-date"] = "2027-01-01"

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_API_KEY="test-api-key",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "no seminar found on that date")
