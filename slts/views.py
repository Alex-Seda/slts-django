from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from django.db import IntegrityError
from django.contrib import messages
from .models import Registration, Attendee, Seminar, SeminarQuerySet
from .services import send_confirmation_email, normalize_phone
from .forms import AttendeeForm


def home(request):
    n_seminar = Seminar.objects.get_next_north_seminar()
    s_seminar = Seminar.objects.get_next_south_seminar()
    template = loader.get_template("slts/pages/home.html")
    context = {"n_seminar": n_seminar, "s_seminar": s_seminar}
    return HttpResponse(template.render(context, request))

def seminars(request):
    campus = request.GET.get("campus", "all")
    seminars_2026 = Seminar.objects.get_seminars_by_year(2026)
    template = loader.get_template("slts/pages/seminars.html")
    context = {
        "campus": campus,
        "seminars_2026": seminars_2026,
    }
    return HttpResponse(template.render(context, request))

def register(request, seminar_id):
    seminar = get_object_or_404(Seminar, pk=seminar_id)
    if not (seminar.status == "scheduled"):
        return redirect('slts:home')
    template = loader.get_template("slts/pages/register.html")
    form = AttendeeForm()
    context = {"form": form, "seminar": seminar}
    return HttpResponse(template.render(context, request))


def register_submit(request, seminar_id):
    form = AttendeeForm(request.POST)   
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])


    # If email or phone is set, prep them for finding attendee
    email = request.POST["email"].lower().strip() if request.POST["email"] else None
    phone = normalize_phone(request.POST["phone"]) if request.POST["phone"] else None
    first_name = request.POST["first_name"].lower()
    seminar = get_object_or_404(Seminar, id=seminar_id)
    attendee = None


    # Ensure that basic contact info is provided. Email or phone at least.
    if not (email or phone):
        messages.error(request, f"You must provide your name and address.\n You must also provide an email AND/OR a phone number.")
        return render(request, "slts/pages/register.html", {"form": form, "seminar": seminar})


    if email:
        attendee = Attendee.objects.filter(
            email=email,
            first_name__iexact=first_name
        ).first()
    
    if not attendee and phone:
        attendee = Attendee.objects.filter(
            phone=phone,
            first_name__iexact=first_name
        ).first()
    
    if not attendee:
        attendee = form.save()


    try:
        Registration.objects.get_or_create(
            attendee=attendee,
            seminar=seminar,
        )

    except:
        messages.error(
            request,
            "We couldn’t process your registration. Please check your spelling and try again."
        )

        return render(
            request,
            "slts/pages/register.html",
            {
                "form": form,       # autopopulate filled in data
                "seminar": seminar,
            },
        )
    

    if email:
        True
        #send_confirmation_email(email, seminar.id)
    
    return redirect("slts:registration_success", seminar_id=seminar_id)


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

