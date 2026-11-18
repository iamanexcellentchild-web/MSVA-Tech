from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra details for a user (filled in on the profile page, or from Google)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True,
                                  help_text="Google's stable user ID ('sub' claim).")
    avatar_url = models.URLField(max_length=500, blank=True, help_text="Photo from the Google account.")
    photo = models.ImageField(upload_to="avatars/", blank=True, help_text="Photo uploaded on the profile page.")
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user}"

    @property
    def avatar(self):
        """Uploaded photo first, then the Google photo, else ''."""
        if self.photo:
            return self.photo.url
        return self.avatar_url
