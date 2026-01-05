from django.urls import path

from . import views


app_name = "slts"

urlpatterns = [
    # frontend pages
    path("", views.index, name="index"),
]
