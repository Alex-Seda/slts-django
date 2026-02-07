from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from .models import Seminar
from .services import export_sign_in_sheet_csv, export_nametags_csv

@staff_member_required
def export_signin(request, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return export_sign_in_sheet_csv(seminar)


@staff_member_required
def export_nametags(request, seminar_id):
    seminar = get_object_or_404(Seminar, id=seminar_id)
    return export_nametags_csv(seminar)
