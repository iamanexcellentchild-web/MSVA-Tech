from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "country", "google_sub", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("google_sub", "avatar_url", "created_at")
