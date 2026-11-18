"""
Authenticate server-rendered page requests using the JWT stored in cookies.

* A valid access-token cookie sets ``request.user``.
* If the access token is missing/expired but the refresh-token cookie is
  valid (and not blacklisted), a new access token is minted transparently
  and written back to the browser on the response.
* Invalid cookies are cleared.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .tokens import clear_auth_cookies, set_access_cookie

User = get_user_model()


def _user_from_token(token):
    user_id = token.get(api_settings.USER_ID_CLAIM)
    if user_id is None:
        return None
    user = User.objects.filter(**{api_settings.USER_ID_FIELD: user_id}).first()
    return user if user and user.is_active else None


class JWTCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw_access = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
        new_access = None
        clear_cookies = False

        user = None
        if raw_access:
            try:
                user = _user_from_token(AccessToken(raw_access))
            except TokenError:
                user = None

        if user is None and raw_refresh:
            try:
                refresh = RefreshToken(raw_refresh)  # also checks the blacklist
                user = _user_from_token(refresh)
                if user is not None:
                    new_access = str(refresh.access_token)
                    # Let DRF views on this same request see the fresh token.
                    request.COOKIES[settings.JWT_AUTH_COOKIE] = new_access
            except TokenError:
                user = None

        if user is not None:
            request.user = user
            request._cached_user = user
        elif raw_access or raw_refresh:
            clear_cookies = True

        response = self.get_response(request)

        # Views (login/logout) that manage cookies themselves take precedence.
        if not getattr(response, "_jwt_cookies_handled", False):
            if new_access:
                set_access_cookie(response, new_access)
            elif clear_cookies:
                clear_auth_cookies(response)
        return response
