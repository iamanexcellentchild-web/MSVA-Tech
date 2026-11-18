"""Helpers for issuing JWTs and storing them in HttpOnly cookies."""

from django.conf import settings
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens(user):
    """Return (access, refresh) JWT strings for the given user."""
    refresh = RefreshToken.for_user(user)
    update_last_login(None, user)
    return str(refresh.access_token), str(refresh)


def _cookie_kwargs():
    return {
        "httponly": True,
        "secure": settings.JWT_COOKIE_SECURE,
        "samesite": settings.JWT_COOKIE_SAMESITE,
        "path": "/",
    }


def set_access_cookie(response, access):
    lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    response.set_cookie(settings.JWT_AUTH_COOKIE, access,
                        max_age=int(lifetime.total_seconds()), **_cookie_kwargs())


def set_auth_cookies(response, access, refresh):
    set_access_cookie(response, access)
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    response.set_cookie(settings.JWT_REFRESH_COOKIE, refresh,
                        max_age=int(lifetime.total_seconds()), **_cookie_kwargs())


def clear_auth_cookies(response):
    for name in (settings.JWT_AUTH_COOKIE, settings.JWT_REFRESH_COOKIE):
        response.delete_cookie(name, path="/", samesite=settings.JWT_COOKIE_SAMESITE)


def blacklist_refresh(raw_refresh):
    """Revoke a refresh token (ignores tokens that are already invalid)."""
    if not raw_refresh:
        return
    try:
        RefreshToken(raw_refresh).blacklist()
    except TokenError:
        pass
