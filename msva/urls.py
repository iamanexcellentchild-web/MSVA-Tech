from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts import api as accounts_api
from core import api as core_api

admin.site.site_header = "MS. Virtual Academy Admin"
admin.site.site_title = "MS. Virtual Academy"
admin.site.index_title = "Academy content & applications"

api_patterns = [
    path("auth/register/", accounts_api.RegisterAPI.as_view(), name="api_register"),
    path("auth/login/", accounts_api.LoginAPI.as_view(), name="api_login"),
    path("auth/google/", accounts_api.GoogleTokenLoginAPI.as_view(), name="api_google_login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api_token_refresh"),
    path("auth/logout/", accounts_api.LogoutAPI.as_view(), name="api_logout"),
    path("auth/me/", accounts_api.MeAPI.as_view(), name="api_me"),
    path("advisor/", core_api.CourseAdvisorAPI.as_view(), name="api_advisor"),
    path("tracks/", core_api.TrackListAPI.as_view(), name="api_tracks"),
    path("tracks/<slug:slug>/", core_api.TrackDetailAPI.as_view(), name="api_track_detail"),
    path("me/applications/", core_api.MyApplicationsAPI.as_view(), name="api_my_applications"),
]

def healthz(request):
    """Uptime/keep-awake ping. Never touches the database, so Neon can still pause."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    path("", include("accounts.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
