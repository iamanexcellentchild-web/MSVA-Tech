"""DRF authentication: `Authorization: Bearer <jwt>` header first, then the HttpOnly cookie."""

from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if not raw_token:
            return None
        try:
            validated = self.get_validated_token(raw_token)
            user = self.get_user(validated)
        except (InvalidToken, TokenError, exceptions.AuthenticationFailed):
            return None  # treat a bad cookie as anonymous instead of failing the request

        # Cookies are sent automatically by browsers, so enforce CSRF like SessionAuthentication.
        self._enforce_csrf(request)
        return user, validated

    @staticmethod
    def _enforce_csrf(request):
        check = CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")
