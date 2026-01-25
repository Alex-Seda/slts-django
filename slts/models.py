import re
import uuid
from django.db import models
from datetime import time, timedelta, date, datetime
from django.utils import timezone
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField


class SeminarQuerySet(models.QuerySet):
    def open_seminars(self):
        return self.filter(status="scheduled")

    def past_seminars(self):
        return self.filter(status="completed")

    def get_next_north_seminar(self):
        return (self.filter(location="north", status="scheduled")
        .order_by("date")
        .first())

    def get_next_south_seminar(self):
        return (self.filter(location="south", status="scheduled")
        .order_by("date")
        .first())

    def get_seminars_by_year(self, year):
        return (self.filter( date__gte=date(year, 1, 1), date__lte=date(year, 12, 31), )
        .exclude(status="draft")
        .order_by("date")
        )
    
    def get_past_seminars_by_year(self,year):
        if year == datetime.now().year:
            filter_string = "-date"
        else:
            filter_string = "date"
        return (self.filter( date__gte=date(year, 1, 1), date__lte=date(year, 12, 31), )
        .filter(status="completed")
        .order_by(filter_string)
        )


class Seminar(models.Model):
    LOCATION_CHOICES = {
        "north": "North Campus (Francis Tuttle)",
        "south": "South Campus (MNTC, S. Penn)",
    }

    SEMINAR_STATUS_CHOICES = {
        "draft" : "Draft",
        "scheduled" : "Scheduled",
        "completed" : "Completed",
    }

    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField(default=time(10,0))
    location = models.CharField(max_length=5, choices=LOCATION_CHOICES)
    status = models.CharField(max_length=9, choices=SEMINAR_STATUS_CHOICES)
    image = models.ImageField(upload_to='seminars/', blank=True)
    handout = models.FileField(upload_to='seminar-handouts/', blank=True)
    url = models.URLField('YouTube URL', blank=True)

    objects = SeminarQuerySet.as_manager()

    def to_embed_url(self):
        youtube_url = self.url
        if not youtube_url:
            return None

        match = re.search(r"(?:v=)([a-zA-Z0-9_-]{11})", youtube_url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"

        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", youtube_url)
        if match:
            return f"https://www.youtube.com/embed/{match.group(1)}"

        return None

    def __str__(self):
        return self.title


class Attendee(models.Model):
    HEARD_FROM_CHOICES = {
        "friend"            : "Friend",
        "edmond l and l"    : "Edmond L&L",
        "bethany tribune"   : "Bethany Tribune",
        "other newspaper"   : "Other Newspaper",
        "flyer"             : "Flyer",
        "facebook"          : "Facebook",
        "website"           : "Website",
        "youtube"           : "YouTube",
        "mailout"           : "Mailout",
        "seminar feedback"  : "Feedback Form / Seminar",
    }

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=40)
    address = models.CharField(max_length=60)
    city = models.CharField(max_length=20)
    state = USStateField(default="OK")
    zip_code = USZipCodeField(blank=True)
    phone = PhoneNumberField(region="US", blank=True)
    email = models.EmailField(blank=True)
    heard_from = models.CharField("Heard About Us From", max_length=16, choices=HEARD_FROM_CHOICES, blank=True)

    def __str__(self):
        return self.first_name + " " + self.last_name + ", " + self.email


class Registration(models.Model):
    REGISTRATION_STATUS_CHOICES = {
        "registered" : "Registered",
        "attended" : "Attended",
        "cancelled" : "Cancelled",
    }
    RATINGS_CHOICES = [(1,1),(2,2),(3,3),(4,4),(5,5)]

    seminar = models.ForeignKey(Seminar, on_delete=models.CASCADE, related_name='registrations')
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name='registrations')
    rating = models.PositiveSmallIntegerField(choices=RATINGS_CHOICES, default=3)
    status = models.CharField(max_length=10, default="registered", choices=REGISTRATION_STATUS_CHOICES)

    def __str__(self):
        return self.attendee.first_name + " " + self.attendee.last_name + " | \"" + self.seminar.title + "\""


class EducationPartner(models.Model):
    LOCATION_CHOICES = {
        "north" : "North",
        "south" : "South",
        "both"  : "Both",
    }

    name = models.CharField(max_length=60)
    image = models.ImageField(upload_to='education-partners/')
    url = models.URLField('Website Link', blank=True)
    description = models.TextField(blank=True)
    partner_location = models.CharField(max_length=5, choices=LOCATION_CHOICES, blank=True)

    def __str__(self):
        return self.name


class FAQ(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField()

    def __str__(self):
        return self.name


class GoogleReview(models.Model):
    name = models.CharField(max_length=60)
    review = models.TextField()

    def __str__(self):
        return self.name

