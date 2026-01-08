from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse


def home(request):
    return render(request, "slts/pages/home.html")

def seminars(request):
    return render(request, "slts/pages/seminars.html")

def recordings(request):
    return render(request, "slts/pages/regordings.html")

def about(request):
    return render(request, "slts/pages/about.html")

