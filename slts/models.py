import re
import uuid
from django.db import models
from datetime import time, timedelta, date, datetime
from django.utils import timezone
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField
from taggit.managers import TaggableManager


class SeminarQuerySet(models.QuerySet):
    def open_seminars(self):
        return self.filter(status="scheduled")

    def past_seminars(self):
        return self.filter(status="completed")

    def get_next_north_seminar(self):
        return (self.filter(location_fk__series="north", status="scheduled")
        .order_by("date")
        .first())

    def get_next_south_seminar(self):
        return (self.filter(location_fk__series="south", status="scheduled")
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
    def get_seminar_by_date(self,date):
        return self.get(date=date)


class AttendeeQuerySet(models.QuerySet):
    def get_attendee_by_name(self, fname, lname):
        return self.get(first_name__iexact=fname, last_name__iexact=lname)


class OtherEventQuerySet(models.QuerySet):
    def get_tours(self):
        return self.filter(event_type='tour').exclude(status="draft").order_by("date")
    def get_expert_insights(self):
        return self.filter(event_type='exin').exclude(status="draft").order_by("date")


class Seminar(models.Model):
    LOCATION_CHOICES = {
        "north": "North Campus (Francis Tuttle)",
        "south": "South Campus (MNTC, S. Penn)",
        "new_north": "North Campus (Portland)",
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
    location = models.CharField(max_length=9, choices=LOCATION_CHOICES)
    location_fk = models.ForeignKey("Location", on_delete=models.PROTECT,verbose_name="Location")
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


class OtherEvent(models.Model):
    EVENT_STATUS_CHOICES = {
        "draft" : "Draft",
        "scheduled" : "Scheduled",
        "completed" : "Completed",
    }

    TYPE_CHOICES = {
        'tour': 'Tour',
        'exin': 'Expert Insights'
    }

    title = models.CharField(max_length=100)
    event_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField(default=time(10,0))
    address = models.CharField(max_length=60)
    city = models.CharField(max_length=20)
    state = USStateField(default="OK")
    zip_code = USZipCodeField(blank=True)
    status = models.CharField(max_length=9, choices=EVENT_STATUS_CHOICES)
    image = models.ImageField(upload_to='events/', blank=True)

    objects = OtherEventQuerySet.as_manager()

    def __str__(self):
        return self.title


class Attendee(models.Model):

    class Meta:
        ordering = ["last_name","first_name"]

    HEARD_FROM_CHOICES = {
        "friend"            : "Friend",
        "edmond l and l"    : "Edmond L&L",
        "bethany tribune"   : "Bethany Tribune",
        "other newspaper"   : "Other Newspaper",
        "news station"      : "News Station",
        "flyer"             : "Flyer",
        "facebook"          : "Facebook",
        "website"           : "Website",
        "youtube"           : "YouTube",
        "internet"          : "Internet",
        "mailout"           : "Mailout",
        "seminar feedback"  : "Feedback Form / Seminar",
        "education partner" : "Education Partner",
    }

    search_fields = ['name']  # required for autocomplete
    autocomplete_fields = ['married_to']  # <-- searchable dropdown

    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=40)
    married_to = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        related_name='spouse',
        null=True,
        blank=True
    )
    address = models.CharField(max_length=60)
    city = models.CharField(max_length=20)
    state = USStateField(default="OK")
    zip_code = USZipCodeField(blank=True)
    phone = PhoneNumberField(region="US", blank=True)
    email = models.EmailField(blank=True)
    heard_from = models.CharField("Heard About Us From", max_length=17, choices=HEARD_FROM_CHOICES, blank=True)
    local = models.BooleanField(default=True)
    deceased = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    birthday = models.DateField(blank=True,null=True)

    objects = AttendeeQuerySet.as_manager()

    def __str__(self):
        return self.first_name + " " + self.last_name + ", " + self.email

    def save(self, *args, **kwargs):
        # Track old spouse before saving
        old_spouse = None
        if self.pk:
            old_spouse = Attendee.objects.filter(pk=self.pk).first().married_to

        super().save(*args, **kwargs)

        # If married_to changed, update the other side
        if old_spouse != self.married_to:
            # Remove old spouse link
            if old_spouse and old_spouse.married_to == self:
                old_spouse.married_to = None
                old_spouse.save()

            # Set new spouse link
            if self.married_to and self.married_to.married_to != self:
                self.married_to.married_to = self
                self.married_to.save()


class Registration(models.Model):
    REGISTRATION_STATUS_CHOICES = {
        "registered" : "Registered",
        "attended" : "Attended",
        "cancelled" : "Cancelled",
    }

    seminar = models.ForeignKey(Seminar, on_delete=models.CASCADE, related_name='registrations')
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=10, default="registered", choices=REGISTRATION_STATUS_CHOICES)

    def __str__(self):
        return self.attendee.first_name + " " + self.attendee.last_name + " | \"" + self.seminar.title + "\""


class EventRegistration(models.Model):
    REGISTRATION_STATUS_CHOICES = {
        "registered" : "Registered",
        "attended" : "Attended",
        "cancelled" : "Cancelled",
    }

    event = models.ForeignKey(OtherEvent, on_delete=models.CASCADE, related_name='eventRegistrations')
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name='eventRegistrations')
    status = models.CharField(max_length=10, default="registered", choices=REGISTRATION_STATUS_CHOICES)

    def __str__(self):
        return self.event.get_event_type_display().upper() + " : " + self.attendee.first_name + " " + self.attendee.last_name + ", \"" + self.event.title + "\""


class EducationPartner(models.Model):
    LOCATION_CHOICES = {
        "north" : "North",
        "south" : "South",
        "both"  : "Both",
    }

    name = models.CharField(max_length=60)
    image = models.ImageField(upload_to='education-partners/')
    url = models.URLField('Website Link', blank=True)
    notes = models.TextField(blank=True)
    partner_location = models.CharField(max_length=5, choices=LOCATION_CHOICES, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FAQ(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField()

    def __str__(self):
        return self.question


class GoogleReview(models.Model):
    name = models.CharField(max_length=60)
    review = models.TextField()

    def __str__(self):
        return self.name

class Location(models.Model):
    SERIES_CHOICES = {
        "north" : "North",
        "south" : "South",
    }

    COLOR_CHOICES = {
        "purple" : "Purple (Primary)",
        "pink" : "Pink",
        "red" : "Red",
        "orange" : "Orange",
        "blue" : "Blue",
        "green" : "Green",
        "lime" : "Lime",
    }

    short_name = models.CharField(max_length=60)
    series = models.CharField(max_length=5, choices=SERIES_CHOICES)
    email_signature = models.TextField()
    color = models.CharField(max_length=6, choices=COLOR_CHOICES)

    def __str__(self):
        return self.short_name + " (" + self.series.title() + ")"
