from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views,admin_views


app_name = "slts"

urlpatterns = [
    # Home Page
    path("", views.home, name="home"),

    # Event Related Pages
    path("<str:event_type>/schedule/", views.schedule, name="schedule"),
    path("<int:year>/seminar_recordings/", views.recordings, name="recordings"),

    # Registration Related Pages
    path("<str:event_type>/<int:event_id>/register/", views.register, name="register"),
    path('<str:event_type>/<int:event_id>/register/submit/', views.register_submit, name='register_submit'),
    path('<str:event_type>/<int:event_id>/registration-success/', views.registration_success, name='registration_success'),

    # Custom Admin Export URLs
    path("attendee-export/", admin_views.export_all_attendees, name='export_attendees_csv'),
    path("<int:year>/attendee-analytics-export/", admin_views.export_attendee_analytics, name='export_attendee_analytics_csv'),

    # Other Pages
    path("education_partners/", views.education_partners, name="education_partners"),
    path("about_us/", views.about, name="about"),
    path("terms-of-use/", views.terms_of_use, name="terms_of_use"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),

    # API URL
    path('api/register/submit/', views.api_register_submit, name='api_register_submit'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
