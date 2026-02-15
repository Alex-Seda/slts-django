from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


app_name = "slts"

urlpatterns = [
    # Home Page
    path("", views.home, name="home"),

    # Seminars Related Pages
    path("<str:event_type>/schedule/", views.schedule, name="schedule"),
    path("<int:year>/seminar_recordings/", views.recordings, name="recordings"),

    # Registration Related Pages
    path("<str:event_type>/<int:event_id>/register/", views.register, name="register"),
    path('seminars/<int:seminar_id>/register/submit/', views.register_submit, name='register_submit'),
    path('<int:seminar_id>/registration-success/', views.registration_success, name='registration_success'),

    # Other Pages
    path("education_partners/", views.education_partners, name="education_partners"),
    path("about_us/", views.about, name="about"),
    path("terms-of-use/", views.terms_of_use, name="terms_of_use"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
