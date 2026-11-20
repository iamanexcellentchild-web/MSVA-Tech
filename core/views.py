from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from .emails import send_application_confirmation, send_contact_notification
from .forms import ApplicationForm, ContactForm
from .models import FAQ, Application, Benefit, Stat, SyllabusWeek, TeamMember, Track


def _published_tracks():
    return Track.objects.filter(is_published=True)


def home(request):
    tracks = _published_tracks()
    return render(request, "core/home.html", {
        "stats": Stat.objects.all(),
        "tracks": tracks,
        "typing_words": [f"{t.title} Experts." for t in tracks] + ["Tech Professionals."],
    })


def about(request):
    return render(request, "core/about.html", {
        "stats": Stat.objects.all(),
        "team": TeamMember.objects.all(),
        "faqs": FAQ.objects.filter(track__isnull=True),
    })


def track_list(request):
    tracks = _published_tracks().prefetch_related("weeks")
    return render(request, "core/track_list.html", {"tracks": tracks})


def track_detail(request, slug):
    track = get_object_or_404(
        _published_tracks().prefetch_related(
            Prefetch("weeks", queryset=SyllabusWeek.objects.order_by("week_number")),
            "faqs",
        ),
        slug=slug,
    )
    application = None
    if request.user.is_authenticated:
        application = Application.objects.filter(user=request.user, track=track).first()

    return render(request, "core/track_detail.html", {
        "track": track,
        "application": application,
        "other_tracks": _published_tracks().exclude(pk=track.pk),
    })


@login_required
def apply(request, slug=None):
    """MS Virtual Scholarship application. Saved to the user's account, so it shows on their dashboard."""
    slug = slug or request.GET.get("track")
    initial = {}
    if slug:
        track = _published_tracks().filter(slug=slug).first()
        if track:
            initial["track"] = track

    form = ApplicationForm(request.POST or None, user=request.user, initial=initial)
    if request.method == "POST" and form.is_valid():
        application = form.save()
        send_application_confirmation(application, request)
        request.session["last_application_id"] = application.pk
        return redirect("core:apply_thanks")

    return render(request, "core/apply.html", {"form": form})


@login_required
def apply_thanks(request):
    app_id = request.session.get("last_application_id")
    application = Application.objects.filter(pk=app_id, user=request.user).select_related("track").first()
    if application is None:
        return redirect("accounts:dashboard")
    return render(request, "core/apply_thanks.html", {"application": application})


def benefits(request):
    return render(request, "core/benefits.html", {"benefits": Benefit.objects.all()})


def team(request):
    return render(request, "core/team.html", {"team": TeamMember.objects.all()})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "GET" and request.user.is_authenticated:
        form.initial = {"name": request.user.get_full_name(), "email": request.user.email}
    if request.method == "POST" and form.is_valid():
        message = form.save()
        send_contact_notification(message, request)
        messages.success(request, "Thanks for reaching out! Our team will get back to you shortly.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form, "faqs": FAQ.objects.filter(track__isnull=True)})


def terms(request):
    return render(request, "core/terms.html")


def csrf_failure(request, reason=""):
    """Friendly page for an expired or invalid form submission (instead of Django's plain 403)."""
    return render(request, "403_csrf.html", status=403)
