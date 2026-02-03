from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from django_summernote.admin import SummernoteModelAdmin
from .models import Attendee, Seminar, Registration, EducationPartner, FAQ, GoogleReview



class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 1


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
        'email',
        'city',
        'heard_from',
        'tag_list'
        # number of seminars attended
    ]

    list_filter = [
        'heard_from',
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
            'notes',
            'married_to',
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

    list_per_page = 10


class UserAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ("is_superuser",)
        return self.readonly_fields
    
    list_per_page = 10


class EducationPartnerAdmin(SummernoteModelAdmin):
    summernote_fields = 'description'

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
        'description',
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



admin.site.register(Seminar, SeminarAdmin)
admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(EducationPartner, EducationPartnerAdmin)
admin.site.register(FAQ, FaqAdmin)
admin.site.register(GoogleReview, GoogleReviewAdmin)
