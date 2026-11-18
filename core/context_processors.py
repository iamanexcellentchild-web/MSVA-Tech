from django.conf import settings

from .models import Track


def site(request):
    return {
        "academy": settings.ACADEMY,
        "nav_tracks": Track.objects.filter(is_published=True).only("title", "slug", "icon"),
    }
