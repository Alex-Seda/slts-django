from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Attendee, Seminar, SeminarQuerySet
from .services import parse_registration_token, send_completion_email


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

    return redirect(f"{reverse('slts:registration_success')}?seminar_id={seminar.id}")


def complete_registration(request):
    token = request.GET.get("token")
    email, seminar_id = parse_registration_token(token)
    seminar = Seminar.objects.get(id=seminar_id)
    template = loader.get_template("slts/pages/complete_registration.html")

    if request.method == "POST":
        form = AttendeeForm(request.POST)
        if form.is_valid():
            attendee = form.save()
            Registration.objects.create(attendee=attendee, seminar=seminar)
            return redirect("registration_success")
    else:
        form = AttendeeForm(initial={"email": email})

    context = {"form": form, "seminar": seminar}

    return HttpResponse(template.render(context, request))


def registration_success(request):
    template = loader.get_template("slts/pages/registration_success.html")
    seminar_id = request.GET.get("seminar_id")
    seminar = None
    if seminar_id:
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

