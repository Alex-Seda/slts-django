import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from django.db import IntegrityError
from django.contrib import messages
from django.conf import settings
from datetime import datetime
from .models import EducationPartner, EventRegistration, Registration, Attendee, Seminar, SeminarQuerySet, OtherEvent, OtherEventQuerySet, FAQ, GoogleReview
from .services import send_confirmation_email, normalize_phone, get_or_create_attendee, get_or_create_spouse, check_api_key, check_registration_info
from .forms import AttendeeForm


def home(request):
    n_seminar = Seminar.objects.get_next_north_seminar()
    s_seminar = Seminar.objects.get_next_south_seminar()
    education_partners = EducationPartner.objects.filter(active=True)
    testimonials = GoogleReview.objects.all()
    faqs = FAQ.objects.all()
    current_year = datetime.now().year
    template = loader.get_template("slts/pages/home.html")
    context = {
        "n_seminar": n_seminar,
        "s_seminar": s_seminar,
        "education_partners": education_partners,
        "testimonials": testimonials,
        "current_year": current_year,
        "faqs": faqs,
    }
    return HttpResponse(template.render(context, request))


def schedule(request, event_type, event_year):
    if(event_type == 'seminars'):
        context = {
            "event_type": "Seminar",
            "event_year": event_year,
            "events": Seminar.objects.get_seminars_by_year(event_year)
        }
    elif(event_type == 'tours'):
        context = {
            "event_type": "Tour",
            "event_year": event_year,
            "events": OtherEvent.objects.get_tours()
        }
    elif(event_type == 'expert-insights'):
        context = {
            "event_type": "Expert Insights",
            "event_year": event_year,
            "events": OtherEvent.objects.get_expert_insights()
        }
    else:
        return redirect('slts:home')

    template = loader.get_template("slts/pages/schedule.html")
    return HttpResponse(template.render(context, request))


def register(request, event_id, event_type):
    form = AttendeeForm()

    if(event_type == 'seminar'):
        event = get_object_or_404(Seminar, pk=event_id)
        context = {"form": form, "event": event, "event_type":"Seminar"}
    elif(event_type == 'tour'):
        event = get_object_or_404(OtherEvent, pk=event_id)
        context = {"form": form, "event": event, "event_type":"Tour"}
    elif(event_type == 'expert-insights'):
        event = get_object_or_404(OtherEvent, pk=event_id)
        context = {"form": form, "event": event, "event_type":"Expert Insights"}
    else:
        return redirect('slts:home')

    # Right now, there is a bug where you can enter tour as the event_type but pick an id
    # that is an expert insights, and it will render the expert insights
    # This happens because they are from the same model. Maybe use the OtherEventQuerySet
    # to use get_object_or_404 but with a filter? 


    if not (event.status == "scheduled"):
        return redirect('slts:home')
    template = loader.get_template("slts/pages/register.html")
    return HttpResponse(template.render(context, request))


def register_submit(request, event_id, event_type):
    if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

    form = AttendeeForm(request.POST)
    allowed = {"seminar", "tour", "expert-insights"}

    # Ensure that the url parameter is an expected value
    if event_type not in allowed:
        previous = request.META.get("HTTP_REFERER")
        if previous:
            return redirect(previous)
        raise Http404()
     
    # Get event object
    if(event_type == 'seminar'):
        event = get_object_or_404(Seminar, pk=event_id)
    else:
        event = get_object_or_404(OtherEvent, pk=event_id)


    # If form does not pass the validation check, do not proceed
    # (This uses the validation functions in the AttendeeForm)
    if not form.is_valid():
        return render(request, "slts/pages/register.html", {"form": form, "event": event, "event_type": event_type},)


    # Get all fields from form submission
    email = request.POST["email"].lower().strip() or ""
    phone = normalize_phone(request.POST.get("phone")) if request.POST.get("phone") else ""
    address = request.POST["address"] or None
    city = request.POST["city"] or None
    zip_code = request.POST["zip_code"] or ""
    heard_from = request.POST["heard_from"] or ""
    first_name = request.POST["first_name"].lower()
    last_name = request.POST["last_name"].lower()
    birthday = form.cleaned_data["birthday"]
    spouse_first_name = request.POST.get("spouse_first_name", "").strip().lower() or None
    attendee = None
    spouse = None


    # Ensure that basic contact info is provided. Email or phone at least.
    if not ((email or phone) and address and city and first_name and last_name and birthday):
        messages.error(request, "You must provide your name, address, and birthday.\n You must also provide an email AND/OR a phone number.")
        return render(request, "slts/pages/register.html", {"form": form, "event": event, "event_type": event_type},)


    try:
        attendee = get_or_create_attendee(first_name, last_name, email, phone, address, city, zip_code, heard_from, birthday)
        if(event_type == 'seminar'):
            Registration.objects.get_or_create(attendee=attendee, seminar=event)
        else:
            EventRegistration.objects.get_or_create(attendee=attendee, event=event)

        # Optional spouse
        if spouse_first_name:
            spouse = get_or_create_spouse(spouse_first_name, last_name, email, phone, address, city, zip_code, heard_from, attendee)
            if(event_type == 'seminar'):
                Registration.objects.get_or_create(attendee=spouse, seminar=event)
            else:
                EventRegistration.objects.get_or_create(attendee=spouse, event=event)

    except Exception as e:
        messages.error(
            request,
            "We couldn’t process your registration. Please check your spelling and try again."
        )
        print("Registration error: ", e)
        return render(request, "slts/pages/register.html", {"form": form, "event": event, "event_type": event_type},)


    if email:
        send_confirmation_email(email, event.id, event_type)

    return redirect("slts:registration_success", event_id=event_id, event_type=event_type)

# Fix this to work for all events
def registration_success(request, event_id, event_type):

    # Ensure that the url parameter is an expected value
    allowed = {"seminar", "tour", "expert-insights"}
    if event_type not in allowed:
        previous = request.META.get("HTTP_REFERER")
        if previous:
            return redirect(previous)
        raise Http404()

    # Get event object
    if(event_type == 'seminar'):
        event = get_object_or_404(Seminar, pk=event_id)
    else:
        event = get_object_or_404(OtherEvent, pk=event_id)

    context = {"event": event}
    template = loader.get_template("slts/pages/registration_success.html")

    return HttpResponse(template.render(context, request))

@csrf_exempt
@require_POST
def api_register_submit(request):
    if not check_api_key(request):
        return JsonResponse({"status": "fail", "error": "unauthorized"}, status=401)

    # Ensure that Seminar (date) and Person (first & last name) are given
    valid, error = check_registration_info(request)
    if not valid:
        return JsonResponse({"status": "fail", "error": error}, status=401)

    # Attempt to retrieve Seminar and Person
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "fail", "error": "error retrieving body"}, status=401)

    seminar_date = data.get("seminar-date", "").strip()
    attendee_first_name = data.get("attendee-first-name", "").strip()
    attendee_last_name = data.get("attendee-last-name", "").strip()

    try:
        seminar = Seminar.objects.get_seminar_by_date(seminar_date)
    except Seminar.DoesNotExist:
        return JsonResponse({"status": "fail", "error": "no seminar found on that date"}, status=404)
    except Seminar.MultipleObjectsReturned:
        return JsonResponse({"status": "fail", "error": "multiple seminars found on that date"}, status=409)

    try:
        attendee = Attendee.objects.get_attendee_by_name(attendee_first_name,attendee_last_name)
    except Attendee.DoesNotExist:
        return JsonResponse({"status": "fail", "error": "no attendee found with the given first/last name"}, status=404)
    except Attendee.MultipleObjectsReturned:
        return JsonResponse({"status": "fail", "error": "multiple attendees found with the given first/last name"}, status=409)

    # Attempt to register Person to Seminar
    try:
        Registration.objects.get_or_create(attendee=attendee, seminar=seminar)
    except Exception as e:
        logger.exception("Registration failed")
        return JsonResponse({"status": "fail", "error": "something went wrong with the registration"}, status=500)

    return JsonResponse({"status": "success"}, status=200)



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
    education_partners = EducationPartner.objects.filter(active=True)
    faqs = FAQ.objects.all()
    template = loader.get_template("slts/pages/about.html")
    context = {"education_partners": education_partners, "faqs": faqs,}
    return HttpResponse(template.render(context, request))

def terms_of_use(request):
    template = loader.get_template("slts/pages/terms_of_use.html")
    context={}
    return HttpResponse(template.render(context, request))

def privacy_policy(request):
    template = loader.get_template("slts/pages/privacy_policy.html")
    context={}
    return HttpResponse(template.render(context, request))
