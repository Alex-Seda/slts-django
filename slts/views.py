from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from .models import Registration, Attendee, Seminar, SeminarQuerySet, RegistrationToken
from .services import parse_registration_token, send_completion_email, send_confirmation_email
from .forms import AttendeeForm


def home(request):
    n_seminar = Seminar.objects.get_next_north_seminar()
    s_seminar = Seminar.objects.get_next_south_seminar()
    template = loader.get_template("slts/pages/home.html")
    context = {"n_seminar": n_seminar, "s_seminar": s_seminar}
    return HttpResponse(template.render(context, request))

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


def register_submit(request, seminar_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    email = request.POST["email"].lower().strip()
    seminar = get_object_or_404(Seminar, id=seminar_id)

    try:
        attendee = Attendee.objects.get(email=email)
    except Attendee.DoesNotExist:
        send_completion_email(email, seminar.id)
        return render(request, "slts/pages/check_email.html")

    Registration.objects.get_or_create(
        attendee=attendee,
        seminar=seminar,
    )

    send_confirmation_email(email, seminar.id)

    return redirect("slts:check_email")


def check_email(request):
    return render(request, "slts/pages/check_email.html")


def complete_registration(request, token):
    # Get token
    token_obj = get_object_or_404(RegistrationToken, token=token)
    print("Token object: ", repr(token_obj))
    print("Token: ", repr(token_obj.token))

    if token_obj.used:
        return HttpResponseBadRequest("Token already used")

    if token_obj.is_expired():
        return HttpResponseBadRequest("Token expired")

    # If token is valid and unused, get info out
    email = token_obj.email
    seminar = token_obj.seminar
    

    # if the request was the user submitting the form, process it and mark the token as used
    if request.method == "POST":
        form = AttendeeForm(request.POST)
        if form.is_valid():
            attendee = form.save()
            Registration.objects.create(attendee=attendee, seminar=seminar)
            token_obj.used = True
            token_obj.save()
            return redirect("slts:registration_success", seminar_id=seminar.id)
    
    # otherwise, return the form for them to fill out
    else:
        form = AttendeeForm(initial={"email": email})
        template = loader.get_template("slts/pages/complete_registration.html")
        context = {"form": form, "seminar": seminar}
        return HttpResponse(template.render(context, request))


def registration_success(request,seminar_id):
    template = loader.get_template("slts/pages/registration_success.html")
    seminar = get_object_or_404(Seminar, id=seminar_id)

    context = {"seminar": seminar}

    return HttpResponse(template.render(context, request))


def recordings(request):
    past_seminars = Seminar.objects.past_seminars()
    template = loader.get_template("slts/pages/recordings.html")
    context = {"past_seminars": past_seminars}
    return HttpResponse(template.render(context, request))

def about(request):
    return render(request, "slts/pages/about.html")

