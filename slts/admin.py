from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from django_summernote.admin import SummernoteModelAdmin
from .models import Attendee, Seminar, Registration, EducationPartner



class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 1



class SeminarAdmin(SummernoteModelAdmin):
    ordering = ("date",)

    def attendance_summary(self, obj):
        count = obj.registrations.count()
        return format_html(
            '<strong style="font-size:20px;">{} attendees</strong>',
            count
        )

    attendance_summary.short_description = "Attendance"


    def average_rating_display(self, obj):
        avg = obj.registrations.aggregate(avg=Avg('rating'))['avg'] or 0
        stars = '★' * round(avg) + '☆' * (5 - round(avg))

        return format_html(
            '<div>      <span style="font-size:32px;">{}</span>     <strong style="font-size:16px;">({})</strong>       </div>',
            stars, avg
        )

    average_rating_display.short_description = "Average Rating"

    readonly_fields = (
        'attendance_summary',
        'average_rating_display',
    )

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
        ('Overview', {'fields': [
            'attendance_summary',
            'average_rating_display',
        ]}),

        ('Edit Content', {'fields': [
            'title',
            'subtitle',
            'status',
            'url',
            'image',
            'description',
        ]}),

        ('Scheduling', {'fields': [
            'date',
            'time',
            'location',
        ]}),
    ]
    inlines = [RegistrationInline]



class AttendeeAdmin(admin.ModelAdmin):
    def attendance_summary(self, obj):
        count = obj.registrations.count()
        if count==1:
            return format_html(
                '<strong style="font-size:16px;">{} seminar attended</strong>',
                count
            )
        else:
            return format_html(
                '<strong style="font-size:16px;">{} seminar(s) attended</strong>',
                count
            )

    attendance_summary.short_description = "Attendance"

    readonly_fields = ('attendance_summary',)

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
            'attendance_summary',
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


class EducationPartnerAdmin(admin.ModelAdmin):
    list_display = [
        'name'
    ]

    search_fields = [
        'name'
    ]




admin.site.register(Seminar, SeminarAdmin)
admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(EducationPartner, EducationPartnerAdmin)
