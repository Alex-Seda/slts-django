from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Attendee, Seminar, Registration

admin.site.register(Attendee)


@admin.register(Seminar)
class RegisterAdmin(SummernoteModelAdmin):
    summernote_fields = 'description'


