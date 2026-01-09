from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Seminar


def home(request):
    return render(request, "slts/pages/home.html")

def seminars(request):
    return render(request, "slts/pages/seminars.html")

def register(request, seminar_id):
    seminar = get_object_or_404(Seminar, pk=seminar_id)
    template = loader.get_template("slts/pages/register.html")
    context = {"seminar": seminar}
    return HttpResponse(template.render(context, request))

def recordings(request):
    return render(request, "slts/pages/regordings.html")

def about(request):
    return render(request, "slts/pages/about.html")

