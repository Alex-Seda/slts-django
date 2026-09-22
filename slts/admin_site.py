from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django_daisy.admin import DaisyAdminSite
from django_daisy.logentry_admin import LogentryAdmin

from .models import Attendee, EventRegistration, OtherEvent, Registration, Seminar


class DashboardAdminSite(DaisyAdminSite):
    site_header = "SLTS Administration"
    site_title = "SLTS Admin"
    index_title = "Dashboard"
    index_template = "admin/index.html"

    def index(self, request, extra_context=None):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        upcoming_seminars = (
            Seminar.objects.filter(date__gte=today, status="scheduled")
            .annotate(registration_count=Count("registrations"))
            .select_related("location_fk")
            .order_by("date", "time")[:5]
        )
        upcoming_events = (
            OtherEvent.objects.filter(date__gte=today, status="scheduled")
            .annotate(registration_count=Count("eventRegistrations"))
            .order_by("date", "time")[:5]
        )

        context = {
            "dashboard_metrics": {
                "attendees": Attendee.objects.count(),
                "upcoming_events": (
                    Seminar.objects.filter(date__gte=today, status="scheduled").count()
                    + OtherEvent.objects.filter(
                        date__gte=today, status="scheduled"
                    ).count()
                ),
                "registrations_this_month": (
                    Registration.objects.filter(
                        seminar__date__gte=month_start,
                        seminar__date__lte=today,
                    ).count()
                    + EventRegistration.objects.filter(
                        event__date__gte=month_start,
                        event__date__lte=today,
                    ).count()
                ),
                "attendance_rate": self._attendance_rate(),
            },
            "upcoming_seminars": upcoming_seminars,
            "upcoming_events": upcoming_events,
            "dashboard_links": [
                {
                    "label": "Add attendee",
                    "description": "Create a new person record",
                    "url": reverse("admin:slts_attendee_add"),
                    "icon": "fa-user-plus",
                    "tone": "purple",
                },
                {
                    "label": "Schedule seminar",
                    "description": "Create an upcoming seminar",
                    "url": reverse("admin:slts_seminar_add"),
                    "icon": "fa-calendar-plus",
                    "tone": "yellow",
                },
                {
                    "label": "Review registrations",
                    "description": "Update attendance status",
                    "url": reverse("admin:slts_registration_changelist"),
                    "icon": "fa-clipboard-list",
                    "tone": "blue",
                },
                {
                    "label": "Export attendee data",
                    "description": "Download the full attendee list",
                    "url": reverse("slts:export_attendees_csv"),
                    "icon": "fa-file-export",
                    "tone": "green",
                },
            ],
        }
        return super().index(request, {**context, **(extra_context or {})})

    @staticmethod
    def _attendance_rate():
        total = (
            Registration.objects.exclude(status="cancelled").count()
            + EventRegistration.objects.exclude(status="cancelled").count()
        )
        attended = (
            Registration.objects.filter(status="attended").count()
            + EventRegistration.objects.filter(status="attended").count()
        )
        return round(attended / total * 100) if total else 0


site = DashboardAdminSite(name="admin")
site.register(LogEntry, LogentryAdmin)
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)
