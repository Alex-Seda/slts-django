from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from django.db import IntegrityError
from django.contrib import messages
from datetime import datetime
from .models import EducationPartner, Registration, Attendee, Seminar, SeminarQuerySet, FAQ, GoogleReview
from .services import send_confirmation_email, normalize_phone
from .forms import AttendeeForm


def home(request):
    n_seminar = Seminar.objects.get_next_north_seminar()
    s_seminar = Seminar.objects.get_next_south_seminar()
    education_partners = EducationPartner.objects.all()
    faqs = FAQ.objects.all()
    current_year = datetime.now().year
    template = loader.get_template("slts/pages/home.html")
    context = {
        "n_seminar": n_seminar, 
        "s_seminar": s_seminar, 
        "education_partners": education_partners, 
        "current_year": current_year,
        "faqs": faqs,
    }
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
    address = request.POST["address"] if request.POST["address"] else None
    city = request.POST["city"] if request.POST["city"] else None
    first_name = request.POST["first_name"].lower()
    last_name = request.POST["last_name"].lower()
    seminar = get_object_or_404(Seminar, id=seminar_id)
    attendee = None


    # Ensure that basic contact info is provided. Email or phone at least.
    if not ((email or phone) and address and city and first_name and last_name):
        messages.error(request, "You must provide your name and address.\n You must also provide an email AND/OR a phone number.")
        return render(request, "slts/pages/register.html", {"form": form, "seminar": seminar})


    elif email:
        attendee = Attendee.objects.filter(
            email=email,
            first_name__iexact=first_name
        ).first()

    elif phone:
        attendee = Attendee.objects.filter(
            phone=phone,
            first_name__iexact=first_name
        ).first()


    try:
        if not attendee:            # The previous lines do not guarantee a match, even if the phone or email exists, so this is not an "elif" or "else"
            attendee = form.save()

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
        send_confirmation_email(email, seminar.id)

    return redirect("slts:registration_success", seminar_id=seminar_id)


def registration_success(request,seminar_id):
    template = loader.get_template("slts/pages/registration_success.html")
    seminar = get_object_or_404(Seminar, id=seminar_id)

    context = {"seminar": seminar}

    return HttpResponse(template.render(context, request))


def recordings(request, year):
    if year>2026 or year<2024:
        return redirect("slts:home")
    past_seminars = Seminar.objects.get_past_seminars_by_year(year)
    template = loader.get_template("slts/pages/recordings.html")
    context = {"past_seminars": past_seminars, "year": year}
    return HttpResponse(template.render(context, request))

def education_partners(request):
    education_partners = EducationPartner.objects.filter(active=True)
    template = loader.get_template("slts/pages/education_partners.html")
    context = {"education_partners": education_partners}
    return HttpResponse(template.render(context, request))

def about(request):
    education_partners = EducationPartner.objects.all()
    faqs = FAQ.objects.all()
    template = loader.get_template("slts/pages/about.html")
    context = {"education_partners": education_partners, "faqs": faqs,}
    return HttpResponse(template.render(context, request))

