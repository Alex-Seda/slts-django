from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Attendee, Seminar, Registration



class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 1



class SeminarAdmin(SummernoteModelAdmin):
    ordering = ("date",)

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
            'image',
            'subtitle',
            'description',
        ]}),

        ('Scheduling', {'fields': [
            'date',
            'time',
            'location',
        ]}),

        ('Other', {'fields': [
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
        ('Attendee Information', {'fields': [
            'first_name',
            'last_name',
            'email',
            'phone',
            'heard_from',
        ]}),

        ('Address', {'fields': [
            'address',
            'city',
            'state',
            'zip_code',
        ]}),

    ]
    inlines = [RegistrationInline]


class UserAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ("is_superuser",)
        return self.readonly_fields




admin.site.register(Seminar, SeminarAdmin)
admin.site.register(Attendee, AttendeeAdmin)
