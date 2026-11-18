"""Google OAuth 2.0 / OpenID Connect helpers."""

from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from .models import Profile

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

User = get_user_model()


class GoogleAuthError(Exception):
    pass


def is_configured():
    return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)


def redirect_uri(request):
    return settings.GOOGLE_OAUTH_REDIRECT_URI or request.build_absolute_uri(
        reverse("accounts:google_callback")
    )


def authorization_url(request, state, nonce):
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "prompt": "select_account",
        "access_type": "online",
    }
    return f"{AUTH_ENDPOINT}?{urlencode(params)}"


def exchange_code(request, code):
    """Swap the authorization code for tokens and return the raw ID token."""
    try:
        resp = requests.post(TOKEN_ENDPOINT, data={
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": redirect_uri(request),
            "grant_type": "authorization_code",
        }, timeout=10)
    except requests.RequestException as exc:
        raise GoogleAuthError("Could not reach Google. Please try again.") from exc

    if resp.status_code != 200:
        raise GoogleAuthError("Google rejected the sign-in request.")
    token = resp.json().get("id_token")
    if not token:
        raise GoogleAuthError("Google did not return an identity token.")
    return token


def verify_id_token(raw_token, nonce=None):
    """Verify signature, audience, issuer and expiry; return the claims."""
    try:
        claims = google_id_token.verify_oauth2_token(
            raw_token, google_requests.Request(), audience=settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError as exc:
        raise GoogleAuthError("Invalid Google identity token.") from exc

    if nonce is not None and claims.get("nonce") != nonce:
        raise GoogleAuthError("Sign-in request could not be verified.")
    if not claims.get("email") or not claims.get("email_verified"):
        raise GoogleAuthError("Your Google account email is not verified.")
    return claims


@transaction.atomic
def get_or_create_user(claims):
    """Find the user by Google ID, then by email; otherwise create a new account."""
    sub = claims["sub"]
    email = claims["email"].lower()

    profile = Profile.objects.select_related("user").filter(google_sub=sub).first()
    user = profile.user if profile else User.objects.filter(email__iexact=email).first()

    if user is None:
        username = email[:150]
        if User.objects.filter(username=username).exists():
            username = f"{email.split('@')[0][:120]}-{sub[-8:]}"
        user = User(username=username, email=email)
        user.set_unusable_password()

    user.first_name = (claims.get("given_name") or user.first_name)[:150]
    user.last_name = (claims.get("family_name") or user.last_name)[:150]
    user.save()

    profile, _ = Profile.objects.get_or_create(user=user)
    profile.google_sub = sub
    profile.avatar_url = claims.get("picture", "")
    profile.save()
    return user
