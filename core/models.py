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
    def image_url(self):
        """Cover uploaded in the admin, else the bundled photo static/images/tracks/<slug>.jpg, else ''."""
        if self.cover_image:
            return self.cover_image.url
        if (settings.BASE_DIR / "static" / "images" / "tracks" / f"{self.slug}.jpg").exists():
            from django.templatetags.static import static
            return static(f"images/tracks/{self.slug}.jpg")
        return ""

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
    """An application to a track (the MS Virtual Scholarship form), tied to the applicant's account."""

    STATUS_CHOICES = [
        ("submitted", "Submitted - Under Review"),
        ("shortlisted", "Shortlisted"),
        ("accepted", "Accepted"),
        ("not_selected", "Not Selected"),
    ]
    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("prefer_not", "Prefer not to say")]
    AGE_CHOICES = [
        ("10-16", "10 - 16"), ("17-25", "17 - 25"), ("26-35", "26 - 35"),
        ("36-50", "36 - 50"), ("51+", "51 and above"),
    ]
    EDUCATION_CHOICES = [
        ("high_school", "High School"),
        ("undergraduate", "Undergraduate"),
        ("degree", "Degree"),
        ("masters", "Masters"),
        ("phd", "PhD"),
        ("nce", "NCE"),
    ]
    REFERRAL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("linkedin", "LinkedIn"),
        ("tiktok", "TikTok"),
        ("friend", "Through a friend"),
        ("family_school", "Through a family member or school official"),
        ("website", "Our website"),
        ("instagram", "Instagram"),
        ("x", "Twitter (X)"),
        ("scholarship_platform", "Scholarship platforms"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="applications", on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name="applications", on_delete=models.CASCADE,
                              verbose_name="Program of choice")

    first_name = models.CharField(max_length=80, default="")
    last_name = models.CharField(max_length=80, default="")
    full_name = models.CharField(max_length=160, editable=False)
    email = models.EmailField()
    gender = models.CharField(max_length=12, choices=GENDER_CHOICES, default="", blank=True)
    phone = models.CharField(max_length=30, help_text="Include the country code, e.g. +234...")
    country = models.CharField(max_length=80, verbose_name="Country of residence")
    city = models.CharField(max_length=80, verbose_name="City of residence")
    age_range = models.CharField(max_length=8, choices=AGE_CHOICES, default="", blank=True, verbose_name="Age")
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES)
    institution = models.CharField(max_length=200, blank=True,
                                   verbose_name="University, college or polytechnic (undergraduates)")
    referral_source = models.CharField(max_length=24, choices=REFERRAL_CHOICES, blank=True,
                                       verbose_name="How did you hear about us?")
    past_student = models.BooleanField(default=False, verbose_name="Past MSVA student")
    student_number = models.CharField(max_length=40, blank=True)
    motivation = models.TextField(blank=True, verbose_name="Why did you choose this program?")
    needs_placement_support = models.BooleanField(
        default=False, verbose_name="Needs priority support for internship and job placement")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    confirmation_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("user", "track")]

    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

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
