from django.urls import path

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
    path('check-email/', views.check_email, name='check_email'),
    path('complete-registration/<uuid:token>/', views.complete_registration, name='complete_registration'),
    path('<int:seminar_id>/registration-success/', views.registration_success, name='registration_success'),

    # Other Pages
    path("about_us/", views.about, name="about"),
]
