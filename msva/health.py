from django.http import HttpResponse


class HealthCheckMiddleware:
    """Answer /healthz/ before host validation, HTTPS redirects, sessions or the database.

    Render's health checker calls the app over plain HTTP from an internal address,
    which would otherwise get a 400 (unknown host) or a 301 (HTTPS redirect).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz/":
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
