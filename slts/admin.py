from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Attendee, Seminar, Registration



class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 1



class SeminarAdmin(SummernoteModelAdmin):
    # Admin table settings
    list_display = [
        'title',
        'date',
        'time',
        'location',
        'status',
    ]

    list_filter = [
        'status',
        'location',
    ]

    search_fields = [
        'title',
    ]

    # Admin add/edit form settings
    summernote_fields = 'description'

    fieldsets = [
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

        ('Visibility', {'fields': [
            'status',
            'url',
        ]}),
    ]
    inlines = [RegistrationInline]



class AttendeeAdmin(admin.ModelAdmin):
    list_display = [
        'first_name',
        'last_name',
        'email',
        'city',
        'state',
        'heard_from',
        # number of seminars attended
    ]

    list_filter = [
        'heard_from',
    ]

    search_fields = [
        'first_name',
        'last_name',
        'address',
        'city',
        'zip_code',
        'phone',
    ]

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
    inlines = [RegistrationInline]




admin.site.register(Seminar, SeminarAdmin)
admin.site.register(Attendee, AttendeeAdmin)
