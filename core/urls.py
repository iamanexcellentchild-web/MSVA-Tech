from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("tracks/", views.track_list, name="track_list"),
    path("tracks/<slug:slug>/", views.track_detail, name="track_detail"),
    path("tracks/<slug:slug>/apply/", views.apply, name="apply_track"),
    path("apply/", views.apply, name="apply"),
    path("apply/thank-you/", views.apply_thanks, name="apply_thanks"),
    path("benefits/", views.benefits, name="benefits"),
    path("team/", views.team, name="team"),
    path("contact/", views.contact, name="contact"),
    path("terms/", views.terms, name="terms"),
]
