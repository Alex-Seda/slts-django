from django.urls import path

from . import views


app_name = "slts"

urlpatterns = [
    # frontend pages
    path("", views.home, name="home"),
    path("seminars/", views.seminars, name="seminars"),
    path("<int:seminar_id>/register/", views.register, name="register"),
    path("seminar_recordings/", views.recordings, name="recordings"),
    path("about_us/", views.about, name="about"),
]
