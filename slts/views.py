from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Seminar, SeminarQuerySet


def home(request):
    return render(request, "slts/pages/home.html")

def seminars(request):
    open_seminars = Seminar.objects.open_seminars()
    template = loader.get_template("slts/pages/seminars.html")
    context = {"open_seminars": open_seminars}
    return HttpResponse(template.render(context, request))

def register(request, seminar_id):
    seminar = get_object_or_404(Seminar, pk=seminar_id)
    template = loader.get_template("slts/pages/register.html")
    context = {"seminar": seminar}
    return HttpResponse(template.render(context, request))

def recordings(request):
    past_seminars = Seminar.objects.past_seminars()
    template = loader.get_template("slts/pages/recordings.html")
    context = {"past_seminars": past_seminars}
    return HttpResponse(template.render(context, request))

def about(request):
    return render(request, "slts/pages/about.html")

