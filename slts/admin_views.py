from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from .models import Seminar
from .services import export_seminar_registrations_csv

@staff_member_required
def seminar_export_csv(request, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return export_seminar_registrations_csv(seminar)
