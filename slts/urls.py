from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views


app_name = "slts"

urlpatterns = [
    # Frontend pages

    # Home Page
    path("", views.home, name="home"),

    # Seminar Related Pages
    path("seminars/", views.seminars, name="seminars"),
    path("seminar_recordings/", views.recordings, name="recordings"),

    # Registration Related Pages
    path("<int:seminar_id>/register/", views.register, name="register"),
    path('seminars/<int:seminar_id>/register/submit/', views.register_submit, name='register_submit'),
    path('<int:seminar_id>/registration-success/', views.registration_success, name='registration_success'),

    # Other Pages
    path("about_us/", views.about, name="about"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
