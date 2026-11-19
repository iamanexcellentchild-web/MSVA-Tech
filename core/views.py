from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm
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
    """Shows the embedded Google Form. ?track=<slug> or /tracks/<slug>/apply/ notes the chosen track."""
    slug = slug or request.GET.get("track")
    track = _published_tracks().filter(slug=slug).first() if slug else None
    request.session["apply_track_slug"] = track.slug if track else None
    return render(request, "core/apply.html", {"track": track})


def apply_thanks(request):
    slug = request.session.get("apply_track_slug")
    track = _published_tracks().filter(slug=slug).first() if slug else None
    return render(request, "core/apply_thanks.html", {"track": track})


def benefits(request):
    return render(request, "core/benefits.html", {"benefits": Benefit.objects.all()})


def team(request):
    return render(request, "core/team.html", {"team": TeamMember.objects.all()})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "GET" and request.user.is_authenticated:
        form.initial = {"name": request.user.get_full_name(), "email": request.user.email}
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks for reaching out! Our team will get back to you shortly.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form, "faqs": FAQ.objects.filter(track__isnull=True)})
