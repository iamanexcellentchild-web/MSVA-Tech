import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import Application, Track

from . import google
from .forms import LoginForm, ProfileForm, SignupForm, UserDetailsForm
from .models import Profile
from .tokens import blacklist_refresh, clear_auth_cookies, issue_tokens, set_auth_cookies


def _safe_next(request, candidate):
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return candidate
    return "/dashboard/"


def _sign_in(user, redirect_to):
    """Issue JWT cookies for the user and redirect."""
    access, refresh = issue_tokens(user)
    response = redirect(redirect_to)
    set_auth_cookies(response, access, refresh)
    response._jwt_cookies_handled = True
    return response


def login_page(request):
    next_url = _safe_next(request, request.GET.get("next") or request.POST.get("next"))
    if request.user.is_authenticated:
        return redirect(next_url)
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        messages.success(request, f"Welcome back, {form.user.first_name or form.user.email}!")
        return _sign_in(form.user, next_url)
    return render(request, "accounts/login.html", {
        "form": form,
        "next": next_url,
        "google_configured": google.is_configured(),
    })


def signup(request):
    next_url = _safe_next(request, request.GET.get("next") or request.POST.get("next"))
    if request.user.is_authenticated:
        return redirect(next_url)
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Welcome to the academy, {user.first_name}! Your account is ready.")
        return _sign_in(user, next_url)
    return render(request, "accounts/signup.html", {
        "form": form,
        "next": next_url,
        "google_configured": google.is_configured(),
    })


def google_login(request):
    """Step 1: redirect the browser to Google's consent screen."""
    if not google.is_configured():
        messages.error(request, "Google sign-in is not configured yet. Please contact the academy.")
        return redirect("accounts:login")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    request.session["google_oauth"] = {
        "state": state,
        "nonce": nonce,
        "next": _safe_next(request, request.GET.get("next")),
    }
    return redirect(google.authorization_url(request, state, nonce))


def google_callback(request):
    """Step 2: Google redirects back here with ?code=...&state=..."""
    flow = request.session.pop("google_oauth", None)

    if request.GET.get("error"):
        messages.info(request, "Google sign-in was cancelled.")
        return redirect("accounts:login")
    if not flow or not secrets.compare_digest(flow["state"], request.GET.get("state", "")):
        messages.error(request, "Your sign-in session expired. Please try again.")
        return redirect("accounts:login")

    try:
        raw_id_token = google.exchange_code(request, request.GET.get("code", ""))
        claims = google.verify_id_token(raw_id_token, nonce=flow["nonce"])
        user = google.get_or_create_user(claims)
    except google.GoogleAuthError as exc:
        messages.error(request, str(exc))
        return redirect("accounts:login")

    if not user.is_active:
        messages.error(request, "This account has been disabled.")
        return redirect("accounts:login")

    messages.success(request, f"Welcome, {user.first_name or user.email}!")
    return _sign_in(user, flow["next"])


@require_POST
def logout_view(request):
    blacklist_refresh(request.COOKIES.get(settings.JWT_REFRESH_COOKIE))
    django_logout(request)
    response = redirect("core:home")
    clear_auth_cookies(response)
    response._jwt_cookies_handled = True
    messages.info(request, "You have been signed out.")
    return response


@login_required
def dashboard(request):
    applications = Application.objects.filter(user=request.user).select_related("track")
    applied_ids = [a.track_id for a in applications]
    profile = getattr(request.user, "profile", None)
    return render(request, "accounts/dashboard.html", {
        "applications": applications,
        "avatar_url": profile.avatar if profile else "",
        "suggested_tracks": Track.objects.filter(is_published=True).exclude(pk__in=applied_ids),
    })


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    has_password = request.user.has_usable_password()
    PasswordForm = PasswordChangeForm if has_password else SetPasswordForm
    action = request.POST.get("action")

    details_form = UserDetailsForm(request.POST if action == "details" else None, instance=request.user)
    profile_form = ProfileForm(request.POST if action == "details" else None,
                               request.FILES if action == "details" else None, instance=profile_obj)
    password_form = PasswordForm(request.user, request.POST if action == "password" else None)

    if action == "details" and details_form.is_valid() and profile_form.is_valid():
        details_form.save()
        profile_form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")

    if action == "password" and password_form.is_valid():
        user = password_form.save()
        # Revoke the old session and sign in again with fresh tokens.
        blacklist_refresh(request.COOKIES.get(settings.JWT_REFRESH_COOKIE))
        messages.success(request, "Your password has been " + ("changed." if has_password else "set. You can now sign in with your email too."))
        return _sign_in(user, "/profile/")

    return render(request, "accounts/profile.html", {
        "details_form": details_form,
        "profile_form": profile_form,
        "password_form": password_form,
        "has_password": has_password,
        "avatar_url": profile_obj.avatar,
        "google_linked": bool(profile_obj.google_sub),
    })
