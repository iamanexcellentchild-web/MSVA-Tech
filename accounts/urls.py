from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("accounts/login/", views.login_page, name="login"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/google/login/", views.google_login, name="google_login"),
    path("accounts/google/callback/", views.google_callback, name="google_callback"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
]
