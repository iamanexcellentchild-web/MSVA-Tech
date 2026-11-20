from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Application, FAQ, Benefit, ContactMessage, Stat, SyllabusWeek, TeamMember, Track,
)


class SyllabusWeekInline(admin.StackedInline):
    model = SyllabusWeek
    extra = 0
    fields = ("week_number", "title", "summary", "topics", "deliverable")


class TrackFAQInline(admin.TabularInline):
    model = FAQ
    extra = 0
    fields = ("order", "question", "answer")


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ("title", "duration", "level", "is_published", "order", "has_syllabus_image")
    list_editable = ("is_published", "order")
    list_filter = ("is_published", "level")
    search_fields = ("title", "short_description", "overview")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("syllabus_image_preview", "cover_image_preview")
    inlines = [SyllabusWeekInline, TrackFAQInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "icon", "tagline", "is_published", "order")}),
        ("Descriptions", {"fields": ("short_description", "overview")}),
        ("Details", {"fields": ("duration", "level", "mode", "certificate")}),
        ("Images", {
            "description": "Upload a syllabus image to display it under the track's syllabus.",
            "fields": (
                "cover_image", "cover_image_preview",
                "syllabus_image", "syllabus_image_caption", "syllabus_image_preview",
            ),
        }),
        ("Lists (one item per line)", {"fields": ("outcomes", "tools", "prerequisites", "career_paths")}),
    )

    @admin.display(boolean=True, description="Syllabus image")
    def has_syllabus_image(self, obj):
        return bool(obj.syllabus_image)

    def _preview(self, image):
        if not image:
            return "No image uploaded."
        return format_html('<img src="{}" style="max-height:220px;border-radius:8px;">', image.url)

    @admin.display(description="Syllabus image preview")
    def syllabus_image_preview(self, obj):
        return self._preview(obj.syllabus_image)

    @admin.display(description="Cover image preview")
    def cover_image_preview(self, obj):
        return self._preview(obj.cover_image)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "track", "order")
    list_filter = ("track",)
    list_editable = ("order",)


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "suffix", "order")
    list_editable = ("value", "suffix", "order")


@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "order")
    list_editable = ("order",)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "order")
    list_editable = ("order",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "track", "email", "phone", "country", "education_level",
                    "status", "confirmation_email_sent", "created_at")
    list_filter = ("status", "track", "education_level", "gender", "age_range", "referral_source",
                   "past_student", "needs_placement_support", "country")
    list_editable = ("status",)
    search_fields = ("full_name", "first_name", "last_name", "email", "phone", "country", "city", "student_number")
    readonly_fields = ("user", "full_name", "confirmation_email_sent", "terms_accepted_at", "created_at", "updated_at")
    date_hierarchy = "created_at"
    fieldsets = (
        ("Program", {"fields": ("track", "status", "user", "created_at", "updated_at", "confirmation_email_sent")}),
        ("Applicant", {"fields": ("first_name", "last_name", "full_name", "email", "gender", "age_range",
                                  "phone", "country", "city")}),
        ("Education", {"fields": ("education_level", "institution", "past_student", "student_number")}),
        ("Other", {"fields": ("referral_source", "motivation", "needs_placement_support", "terms_accepted_at")}),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_resolved", "created_at")
    list_filter = ("is_resolved",)
    list_editable = ("is_resolved",)
    search_fields = ("name", "email", "subject", "message")
