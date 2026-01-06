from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Attendee, Seminar, Registration



class SeminarAdmin(SummernoteModelAdmin):
    summernote_fields = 'description'

    fieldsets = [
        (' ', {'fields': [
            'status',
            'url',
        ]}),

        ('Content', {'fields': [
            'title',
            'subtitle',
            'description',
        ]}),

        ('Scheduling', {'fields': [
            'date',
            'time',
            'location',
        ]}),
    ]



class AttendeeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Name / Email', {'fields': [
            'first_name',
            'last_name',
            'email',
        ]}),

        ('Address', {'fields': [
            'address',
            'city',
            'state',
            'zip_code',
        ]}),

        ('Other Information', {'fields': [
            'phone',
            'heard_from',
        ]}),
    ]




admin.site.register(Seminar, SeminarAdmin)
admin.site.register(Attendee, AttendeeAdmin)
