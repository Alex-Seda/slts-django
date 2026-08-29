import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Seminar, Attendee, Registration, EventRegistration, OtherEvent
from .services import export_sign_in_sheet_csv, export_nametags_csv, export_attendees_raw_csv
from collections import defaultdict
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear



@staff_member_required
def export_signin(request, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return export_sign_in_sheet_csv(seminar)


@staff_member_required
def export_nametags(request, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return export_nametags_csv(seminar)


@staff_member_required
def export_raw(request, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return export_attendees_raw_csv(seminar)

@staff_member_required
def export_all_attendees(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendees.csv"'

    writer = csv.writer(response)
    writer.writerow(["First Name", "Last Name", "Email", "Phone", "Address", "City", "Zip", "Birthday"])
    for a in Attendee.objects.all().order_by("last_name", "first_name"):
        writer.writerow([a.first_name, a.last_name, a.email, a.phone, a.address, a.city, a.zip_code, a.birthday.strftime("%B %-d, %Y") if a.birthday else "",])

    return response

def export_attendee_analytics(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendee_analytics.csv"'

    # e.g. {"tour": "Tour", "exin": "Expert Insights"}
    event_type_labels = OtherEvent.TYPE_CHOICES
    event_type_keys = list(event_type_labels.keys())

    # data[year]["seminar" | event_type]["registered"/"attended"] = count
    data = defaultdict(lambda: defaultdict(lambda: {"registered": 0, "attended": 0}))

    seminar_rows = (
        Registration.objects
        .annotate(year=ExtractYear("seminar__date"))
        .values("year")
        .annotate(
            registered=Count("id"),
            attended=Count("id", filter=Q(status="attended")),
        )
    )
    for row in seminar_rows:
        data[row["year"]]["seminar"]["registered"] = row["registered"]
        data[row["year"]]["seminar"]["attended"] = row["attended"]

    event_rows = (
        EventRegistration.objects
        .annotate(year=ExtractYear("event__date"))
        .values("year", "event__event_type")
        .annotate(
            registered=Count("id"),
            attended=Count("id", filter=Q(status="attended")),
        )
    )
    for row in event_rows:
        event_type = row["event__event_type"]
        data[row["year"]][event_type]["registered"] = row["registered"]
        data[row["year"]][event_type]["attended"] = row["attended"]

    years = sorted(data.keys())

    header = ["Year", "Seminar Registrations", "Seminar Attendance"]
    for key in event_type_keys:
        label = event_type_labels[key]
        header += [f"{label} Registrations", f"{label} Attendance"]

    writer = csv.writer(response)
    writer.writerow(header)

    for yr in years:
        row = [yr, data[yr]["seminar"]["registered"], data[yr]["seminar"]["attended"]]
        for key in event_type_keys:
            row += [data[yr][key]["registered"], data[yr][key]["attended"]]
        writer.writerow(row)

    return response
