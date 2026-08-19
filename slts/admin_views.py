import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Seminar, Attendee
from .services import export_sign_in_sheet_csv, export_nametags_csv, export_attendees_raw_csv

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

def export_attendee_analytics(request, year):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendee_analytics.csv"'

    total_registered=200
    total_attended=150

    writer = csv.writer(response)
    writer.writerow(["Total Registered", "Total Attended"])
    writer.writerow([total_registered,total_attended])

    return response
