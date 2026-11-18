"""
JSON auth endpoints for API clients (mobile apps, a future SPA, etc.).

POST /api/auth/register/        {"first_name", "last_name", "email", "password"} -> 201 {"access", "refresh", "user"}
POST /api/auth/login/           {"email", "password"}             -> {"access", "refresh", "user"}
POST /api/auth/google/          {"id_token": "<Google ID token>"} -> {"access", "refresh", "user"}
POST /api/auth/token/refresh/   {"refresh": "..."}                -> {"access", "refresh"}
POST /api/auth/logout/          {"refresh": "..."}                -> 205
GET  /api/auth/me/              (Authorization: Bearer <access>)
"""

from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import google
from .forms import LoginForm, SignupForm
from .tokens import blacklist_refresh, issue_tokens


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, user):
        profile = getattr(user, "profile", None)
        url = profile.avatar if profile else ""
        request = self.context.get("request")
        if url and url.startswith("/") and request is not None:
            url = request.build_absolute_uri(url)
        return url


def _token_response(request, user, status_code=status.HTTP_200_OK):
    access, refresh = issue_tokens(user)
    return Response({"access": access, "refresh": refresh,
                     "user": UserSerializer(user, context={"request": request}).data}, status=status_code)


def _form_errors(form):
    errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
    if "__all__" in errors:
        errors["detail"] = " ".join(errors.pop("__all__"))
    return errors


class RegisterAPI(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = {
            "first_name": request.data.get("first_name", ""),
            "last_name": request.data.get("last_name", ""),
            "email": request.data.get("email", ""),
            "password1": request.data.get("password", ""),
            # Clients send the password once; confirmation is a UI concern.
            "password2": request.data.get("password", ""),
        }
        form = SignupForm(data)
        if not form.is_valid():
            errors = _form_errors(form)
            if "password1" in errors:
                errors["password"] = errors.pop("password1")
            errors.pop("password2", None)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return _token_response(request, form.save(), status.HTTP_201_CREATED)


class LoginAPI(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        form = LoginForm({"email": request.data.get("email", ""), "password": request.data.get("password", "")},
                         request=request._request)
        if not form.is_valid():
            errors = _form_errors(form)
            code = status.HTTP_401_UNAUTHORIZED if set(errors) == {"detail"} else status.HTTP_400_BAD_REQUEST
            return Response(errors, status=code)
        return _token_response(request, form.user)


class GoogleTokenLoginAPI(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw = request.data.get("id_token") or request.data.get("credential")
        if not raw:
            return Response({"detail": "id_token is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not google.is_configured():
            return Response({"detail": "Google sign-in is not configured."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            user = google.get_or_create_user(google.verify_id_token(raw))
        except google.GoogleAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({"detail": "Account disabled."}, status=status.HTTP_403_FORBIDDEN)

        return _token_response(request, user)


class LogoutAPI(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        blacklist_refresh(request.data.get("refresh"))
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)
