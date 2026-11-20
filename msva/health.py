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


class NoCacheHTMLMiddleware:
    """Pages contain per-visitor content (menus, CSRF tokens), so CDNs such as Netlify must not cache them."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith(("/static/", "/media/")) and "Cache-Control" not in response:
            response["Cache-Control"] = "private, no-cache, no-store, max-age=0"
            response["Netlify-CDN-Cache-Control"] = "no-store"
        return response
