from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def _lines(text):
    """Split a newline-separated admin text field into a clean list."""
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class Track(OrderedModel):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("beginner-intermediate", "Beginner to Intermediate"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    icon = models.CharField(
        max_length=60, default="fa-solid fa-laptop-code",
        help_text="Font Awesome classes, e.g. 'fa-solid fa-shield-halved'.",
    )
    tagline = models.CharField(max_length=200, blank=True)
    short_description = models.TextField(help_text="Shown on track cards.")
    overview = models.TextField(help_text="Full introduction shown on the track page.")

    duration = models.CharField(max_length=60, default="6 Weeks")
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES, default="beginner-intermediate")
    mode = models.CharField(max_length=80, default="Live & Recorded Online Sessions")
    certificate = models.CharField(max_length=120, default="Certificate of Completion")

    cover_image = models.ImageField(
        upload_to="tracks/covers/", blank=True,
        help_text="Optional banner image shown at the top of the track page and on cards.",
    )
    syllabus_image = models.ImageField(
        upload_to="tracks/syllabus/", blank=True,
        help_text="Image of the syllabus/curriculum, shown under the track's week-by-week syllabus.",
    )
    syllabus_image_caption = models.CharField(max_length=200, blank=True)

    outcomes = models.TextField(blank=True, help_text="One learning outcome per line.")
    tools = models.TextField(blank=True, help_text="One tool/technology per line.")
    prerequisites = models.TextField(blank=True, help_text="One prerequisite per line.")
    career_paths = models.TextField(blank=True, help_text="One career path/job role per line.")

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:track_detail", kwargs={"slug": self.slug})

    @property
    def outcome_list(self):
        return _lines(self.outcomes)

    @property
    def tool_list(self):
        return _lines(self.tools)

    @property
    def prerequisite_list(self):
        return _lines(self.prerequisites)

    @property
    def career_path_list(self):
        return _lines(self.career_paths)


class SyllabusWeek(models.Model):
    track = models.ForeignKey(Track, related_name="weeks", on_delete=models.CASCADE)
    week_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    topics = models.TextField(blank=True, help_text="One topic per line.")
    deliverable = models.CharField(max_length=200, blank=True, help_text="Assignment / project for the week.")

    class Meta:
        ordering = ["week_number"]
        unique_together = [("track", "week_number")]

    def __str__(self):
        return f"{self.track} - Week {self.week_number}"

    @property
    def topic_list(self):
        return _lines(self.topics)


class FAQ(OrderedModel):
    track = models.ForeignKey(
        Track, related_name="faqs", on_delete=models.CASCADE, null=True, blank=True,
        help_text="Leave empty for a general academy FAQ.",
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()

    class Meta(OrderedModel.Meta):
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class Stat(OrderedModel):
    label = models.CharField(max_length=120)
    value = models.PositiveIntegerField()
    suffix = models.CharField(max_length=5, blank=True, default="+")
    icon = models.CharField(max_length=60, default="fa-solid fa-star")

    def __str__(self):
        return f"{self.value}{self.suffix} {self.label}"


class Benefit(OrderedModel):
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=60, default="fa-solid fa-circle-check")

    def __str__(self):
        return self.title


class TeamMember(OrderedModel):
    name = models.CharField(max_length=120)
    role_heading = models.CharField(max_length=120, help_text="Section heading, e.g. 'FOUNDER & CEO'.")
    title = models.CharField(max_length=160, help_text="Title shown under the name.")
    bio = models.TextField()
    photo = models.ImageField(upload_to="team/", blank=True)

    def __str__(self):
        return self.name


class Application(models.Model):
    """A student's application to a track, submitted through the site's application form."""

    STATUS_CHOICES = [
        ("submitted", "Submitted - Under Review"),
        ("shortlisted", "Shortlisted"),
        ("accepted", "Accepted"),
        ("not_selected", "Not Selected"),
    ]
    EDUCATION_CHOICES = [
        ("secondary", "Secondary School"),
        ("undergraduate", "Undergraduate / Student"),
        ("graduate", "Graduate (BSc/HND)"),
        ("postgraduate", "Postgraduate"),
        ("other", "Other"),
    ]
    EXPERIENCE_CHOICES = [
        ("none", "No experience - complete beginner"),
        ("some", "Some self-taught experience"),
        ("intermediate", "Intermediate - built small projects"),
        ("advanced", "Advanced - working in the field"),
    ]
    REFERRAL_CHOICES = [
        ("youtube", "YouTube"),
        ("instagram", "Instagram"),
        ("linkedin", "LinkedIn"),
        ("x", "X (Twitter)"),
        ("friend", "Friend / Referral"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="applications", on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name="applications", on_delete=models.CASCADE)

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, help_text="Include country code, e.g. +234...")
    country = models.CharField(max_length=80)
    city = models.CharField(max_length=80, blank=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES)
    has_laptop = models.BooleanField(default=False, verbose_name="Has a laptop & internet access")
    weekly_hours = models.PositiveIntegerField(default=10, verbose_name="Hours available per week")
    motivation = models.TextField(verbose_name="Why do you want to join this track?")
    referral_source = models.CharField(max_length=20, choices=REFERRAL_CHOICES, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    confirmation_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("user", "track")]

    def __str__(self):
        return f"{self.full_name} -> {self.track}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.email})"
