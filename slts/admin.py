import csv
from django.urls import path, reverse
from django.contrib import admin,messages
from django.utils.html import format_html
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Avg, Count
from django_summernote.admin import SummernoteModelAdmin
from .admin_views import export_signin, export_nametags, export_raw
from .models import Attendee, Seminar, OtherEvent, Registration, EventRegistration, EducationPartner, FAQ, GoogleReview, Location



class RegistrationInline(admin.TabularInline):
    model = Registration
    autocomplete_fields = ['attendee', 'seminar']
    extra = 0
    verbose_name = "Seminar Registration"
    verbose_name_plural = "Seminar Registrations"

class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    autocomplete_fields = ['attendee', 'event']
    extra = 0
    verbose_name = "Other Event Registration"
    verbose_name_plural = "Other Event Registrations"


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

    # Link to registrations page
    def view_registrations_link(self, obj):
        # link to Registration changelist filtered by this seminar
        url = reverse("admin:slts_registration_changelist") + f"?seminar__id__exact={obj.id}"
        return format_html('<a href="{}">View All Registrations</a>', url)
    view_registrations_link.short_description = "Registrations"

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
            path(
                "<int:seminar_id>/export_raw/",
                self.admin_site.admin_view(export_raw),
                name="seminar_export_raw"
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
        extra_context["seminar_export_raw"] = reverse(
            "admin:seminar_export_raw",
            args=[object_id],
        )
        return super().change_view(request, object_id, form_url, extra_context)



    readonly_fields = (
        'attendance_summary',
    )

    # Admin table settings
    list_display = [
        'title',
        'date',
        'location_fk',
        'status',
        'view_registrations_link',
    ]

    list_filter = [
        'status',
        'location_fk',
    ]

    search_fields = [
        'title',
    ]

    # Admin add/edit form settings
    summernote_fields = 'description'

    fieldsets = [
        ('Overview', {'fields': [
            'attendance_summary',
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
            'location_fk',
        ]}),
    ]
    #inlines = [RegistrationInline]



class AttendeeAdmin(admin.ModelAdmin):
    change_list_template = "admin/slts/attendee/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "export-filtered/",
                self.admin_site.admin_view(self.export_filtered),
                name="attendee_export_filtered_csv",
            ),
        ]
        return custom + urls

    def export_filtered(self, request):
        cl = self.get_changelist_instance(request)

        if not request.GET:
            messages.error(request, "You must filter the attendees before exporting.")
            return redirect("admin:slts_attendee_changelist")

        queryset = cl.get_queryset(request)  # respects tags filter, search, ordering — no pagination
    
        model = self.model
        exclude = {"id", "married_to", "local", "deceased"}
        field_names = [f.name for f in model._meta.fields if f.name not in exclude]
        header_names = [f.name.replace("_"," ").title() for f in model._meta.fields if f.name not in exclude]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="filtered_attendees.csv"'
        writer = csv.writer(response)
        writer.writerow(header_names)
        for a in queryset:
            writer.writerow([getattr(a, f) for f in field_names])
        return response

    def registration_summary(self, obj):
        if obj is None:
            return "—"

        count = obj.registrations.filter(status="registered").count()
        return format_html(
            '<strong style="font-size:16px;">{} Seminar(s) Currently Registered For</strong>',
            count
        )
    registration_summary.short_description = "Registrations"

    def attendance_summary(self, obj):
        if obj is None:
            return "—"

        count = obj.registrations.filter(status="attended").count()
        return format_html(
            '<strong style="font-size:16px;">{} Seminar(s) Attended</strong>',
            count
        )
    attendance_summary.short_description = "Attendance"

    def cancellation_summary(self, obj):
        if obj is None:
            return "—"

        count = obj.registrations.filter(status="cancelled").count()
        return format_html(
            '<strong style="font-size:16px;">{} Seminar(s) Cancelled / No Show</strong>',
            count
        )
    cancellation_summary.short_description = "Cancellations"

    def other_events_registration_summary(self, obj):
        if obj is None:
            return "—"

        count = obj.eventRegistrations.filter(status="registered").count()
        return format_html(
            '<strong style="font-size:16px;">{} Other Event(s) Currently Registered For</strong>',
            count
        )
    other_events_registration_summary.short_description = "Other Event Registrations"

    def other_events_attendance_summary(self, obj):
        if obj is None:
            return "—"

        count = obj.eventRegistrations.filter(status="attended").count()
        return format_html(
            '<strong style="font-size:16px;">{} Other Event(s) Attended</strong>',
            count
        )
    other_events_attendance_summary.short_description = "Other Event Attendance"

    def other_events_cancellation_summary(self, obj):
        if obj is None:
            return "—"

        count = obj.eventRegistrations.filter(status="cancelled").count()
        return format_html(
            '<strong style="font-size:16px;">{} Other Event(s) Cancelled / No Show</strong>',
            count
        )
    other_events_cancellation_summary.short_description = "Other Event Cancellations"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())

    autocomplete_fields = ['married_to']  # <-- searchable dropdown
    readonly_fields = [
        'registration_summary',
        'attendance_summary',
        'cancellation_summary',
        'other_events_registration_summary',
        'other_events_attendance_summary',
        'other_events_cancellation_summary'
    ]

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
        ]}),

        ('Attendance Statistics', {'fields': [
            'registration_summary',
            'attendance_summary',
            'cancellation_summary',
            'other_events_registration_summary',
            'other_events_attendance_summary',
            'other_events_cancellation_summary',
        ]}),

        ('Address', {'fields': [
            'address',
            'city',
            'state',
            'zip_code',
        ]}),

    ]
    inlines = [RegistrationInline, EventRegistrationInline]

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
        'address'
    ]

    list_display = [
        'title',
        'date',
        'event_type',
        'address',
        'status'
    ]

    list_filter = [
        'event_type',
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
            'address',
            'city',
            'state',
            'zip_code'
        ]}),
    ]
    inlines = [EventRegistrationInline]

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('attendee', 'seminar', 'status')
    list_filter = ('seminar','status')
    search_fields = ('attendee__first_name', 'attendee__last_name', 'seminar__title')
    autocomplete_fields = ('attendee', 'seminar')
    list_per_page = 10

    actions = ['mark_attended','mark_cancelled']

    @admin.action(description="Mark selected registrations as Attended")
    def mark_attended(self, request, queryset):
        updated = queryset.update(status='attended')
        self.message_user(
            request, f"{updated} registration(s) marked as attended."
        )

    @admin.action(description="Mark selected registrations as Cancelled")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(
            request, f"{updated} registration(s) marked as cancelled."
        )

    # Make attendee and seminar editable only when adding a registration
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['attendee','seminar']
        return []

    fieldsets = [
        ('Registration', {'fields': [
            'attendee',
            'seminar',
            'status',
        ]})
    ]


class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('attendee', 'event', 'status')
    list_filter = ('event','status')
    search_fields = ('attendee__first_name', 'attendee__last_name', 'event__title')
    autocomplete_fields = ('attendee', 'event')
    list_per_page = 10

    actions = ['mark_attended','mark_cancelled']

    @admin.action(description="Mark selected registrations as Attended")
    def mark_attended(self, request, queryset):
        updated = queryset.update(status='attended')
        self.message_user(
            request, f"{updated} registration(s) marked as attended."
        )

    @admin.action(description="Mark selected registrations as Cancelled")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(
            request, f"{updated} registration(s) marked as cancelled."
        )

    # Make attendee and seminar editable only when adding a registration
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['attendee','event']
        return []

    fieldsets = [
        ('Registration', {'fields': [
            'attendee',
            'event',
            'status',
        ]})
    ]


class LocationAdmin(admin.ModelAdmin):
    list_per_page = 10

    list_display = [
        'name',
        'series',
        'address',
        'city',
        'color',
    ]

    list_filter = [
        'series',
    ]

    search_fields = [
        'name',
        'address',
    ]


admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Seminar, SeminarAdmin)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(OtherEvent, OtherEventAdmin)
admin.site.register(EventRegistration, EventRegistrationAdmin)
admin.site.register(EducationPartner, EducationPartnerAdmin)
admin.site.register(FAQ, FaqAdmin)
admin.site.register(GoogleReview, GoogleReviewAdmin)
admin.site.register(Location, LocationAdmin)
