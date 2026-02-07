import csv
from django.urls import path, reverse
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from django_summernote.admin import SummernoteModelAdmin
from .admin_views import export_signin, export_nametags
from .models import Attendee, Seminar, OtherEvent, Registration, EventRegistration, EducationPartner, FAQ, GoogleReview



class RegistrationInline(admin.TabularInline):
    model = Registration
    autocomplete_fields = ['attendee', 'seminar']
    extra = 0

class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    autocomplete_fields = ['attendee', 'event']
    extra = 0


class TagListFilter(admin.SimpleListFilter):
    title = ('tag')  # Display title in admin
    parameter_name = 'tag'  # URL query parameter

    def lookups(self, request, model_admin):
        # Return a list of (value, label) for the filter options
        tags = set(t.name for t in model_admin.model.tags.all())  # naive, only works for small sets
        return [(tag, tag) for tag in tags]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__name=self.value())
        return queryset




class SeminarAdmin(SummernoteModelAdmin):
    ordering = ("-date",)
    list_per_page = 10
    change_form_template = "admin/seminar_change_form.html"



    # Attendance Summary for quick view of registrations
    def attendance_summary(self, obj):
        count = obj.registrations.count()
        return format_html(
            '<strong style="font-size:20px;">{} attendees</strong>',
            count
        )
    attendance_summary.short_description = "Attendance"

    # Average rating for quick view of seminar ratings
    def average_rating_display(self, obj):
        avg = obj.registrations.aggregate(avg=Avg('rating'))['avg'] or 0
        stars = '★' * round(avg) + '☆' * (5 - round(avg))

        return format_html(
            '<div>      <span style="font-size:32px;">{}</span>     <strong style="font-size:16px;">({})</strong>       </div>',
            stars, avg
        )
    average_rating_display.short_description = "Average Rating"

    # Add Export URL for Post Requests
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:seminar_id>/export_sign_in/",
                self.admin_site.admin_view(export_signin),
                name="seminar_export_signin",
            ),
            path(
                "<int:seminar_id>/export_nametags/",
                self.admin_site.admin_view(export_nametags),
                name="seminar_export_nametags",
            ),
        ]
        return custom_urls + urls

    # Add the export buttons to the Edit Seminar Page
    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["seminar_export_signin"] = reverse(
            "admin:seminar_export_signin",
            args=[object_id],
        )
        extra_context["seminar_export_nametags"] = reverse(
            "admin:seminar_export_nametags",
            args=[object_id],
        )
        return super().change_view(request, object_id, form_url, extra_context)



    readonly_fields = (
        'attendance_summary',
        'average_rating_display',
    )

    # Admin table settings
    list_display = [
        'title',
        'date',
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
            'handout',
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
        if obj is None:
            return "—"

        count = obj.registrations.count()
        if count == 1:
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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    search_fields = ['name']  # required for autocomplete
    autocomplete_fields = ['married_to']  # <-- searchable dropdown    
    readonly_fields = ['attendance_summary']

    list_display = [
        'first_name',
        'last_name',
        'city',
        'heard_from',
        'tag_list'
        # number of seminars attended
    ]

    list_filter = [
        'heard_from',
        'local',
        'deceased',
        TagListFilter
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
            'tags',
            'local',
            'deceased',
            'notes',
            'married_to',
            'birthday',
            'email',
            'phone',
            'heard_from',
            'attendance_summary'
        ]}),

        ('Address', {'fields': [
            'address',
            'city',
            'state',
            'zip_code',
        ]}),

    ]
    inlines = [RegistrationInline]

    list_per_page = 10


class UserAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ("is_superuser",)
        return self.readonly_fields

    list_per_page = 10


class EducationPartnerAdmin(SummernoteModelAdmin):
    list_per_page = 10

    list_display = [
        'name',
        'partner_location',
        'active'
    ]

    list_filter = [
        'partner_location',
        'active'
    ]

    search_fields = [
        'name'
    ]

    fields = [
        'name',
        'partner_location',
        'active',
        'image',
        'url',
        'notes',
    ]


class FaqAdmin(admin.ModelAdmin):
    list_per_page = 10

    list_display = [
        'question',
    ]

    search_fields = [
        'question',
    ]


class GoogleReviewAdmin(admin.ModelAdmin):
    list_per_page = 10

    list_display = [
        'name',
    ]

    search_fields = [
        'name',
    ]

class OtherEventAdmin(SummernoteModelAdmin):
    ordering = ('-date',)
    list_per_page = 10

    search_fields = [
        'title',
    ]

    list_display = [
        'title',
        'date',
        'event_type',
        'location',
        'status'
    ]

    list_filter = [
        'event_type',
        'location',
        'status'
    ]

    summernote_fields = 'description'

    fieldsets = [
        ('Content', {'fields': [
            'title',
            'event_type',
            'status',
            'image',
            'description',
        ]}),

        ('Scheduling', {'fields': [
            'date',
            'time',
            'location',
        ]}),
    ]
    inlines = [EventRegistrationInline]


admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Seminar, SeminarAdmin)
admin.site.register(OtherEvent, OtherEventAdmin)
admin.site.register(EducationPartner, EducationPartnerAdmin)
admin.site.register(FAQ, FaqAdmin)
admin.site.register(GoogleReview, GoogleReviewAdmin)
