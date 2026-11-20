from django import forms
from django.utils import timezone

from .models import Application, ContactMessage, Track


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "subject": forms.TextInput(attrs={"placeholder": "What is this about?"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Write your message..."}),
        }



class ApplicationForm(forms.ModelForm):
    """Native version of the MS Virtual Scholarship (The Achievers) Google Form."""

    YES_NO = [("yes", "Yes"), ("no", "No")]

    past_student_choice = forms.ChoiceField(
        choices=YES_NO, widget=forms.RadioSelect,
        label="Were you a past MSVA student?",
        help_text="All past students still benefit from stipends and internship opportunities.",
    )
    placement_choice = forms.ChoiceField(
        choices=YES_NO, widget=forms.RadioSelect,
        label="Would you need priority support from MSVA towards internship and job placement?",
    )
    accept_terms = forms.BooleanField(
        required=True,
        label="I have read and agree to the Terms and Conditions",
        error_messages={"required": "Please read and accept the Terms and Conditions to submit your application."},
    )

    class Meta:
        model = Application
        fields = [
            "first_name", "last_name", "email", "gender", "phone", "country", "city", "age_range",
            "education_level", "institution", "referral_source", "student_number", "track", "motivation",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"readonly": "readonly"}),
            "gender": forms.RadioSelect,
            "phone": forms.TextInput(attrs={"placeholder": "+234 800 000 0000", "autocomplete": "tel"}),
            "country": forms.TextInput(attrs={"placeholder": "e.g. Nigeria", "autocomplete": "country-name"}),
            "city": forms.TextInput(attrs={"placeholder": "e.g. Lagos", "autocomplete": "address-level2"}),
            "age_range": forms.RadioSelect,
            "education_level": forms.RadioSelect,
            "institution": forms.TextInput(attrs={"placeholder": "Name of your university, college or polytechnic"}),
            "referral_source": forms.RadioSelect,
            "student_number": forms.TextInput(attrs={"placeholder": "Your MSVA student number"}),
            "track": forms.RadioSelect,
            "motivation": forms.Textarea(attrs={"rows": 4, "placeholder": "Just be brief..."}),
        }
        labels = {
            "phone": "Phone number (include country code)",
            "education_level": "Educational level",
            "institution": "If you are an undergraduate, the name of your university, college or polytechnic",
            "student_number": "Your MSVA student number",
            "track": "Program of choice",
            "motivation": "Why did you choose this program? (just be brief)",
            "age_range": "Age",
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for name in ["gender", "phone", "country", "city", "age_range", "education_level", "referral_source", "track"]:
            self.fields[name].required = True
        self.fields["track"].queryset = Track.objects.filter(is_published=True)
        self.fields["track"].empty_label = None
        for name in ["gender", "age_range", "education_level", "referral_source"]:
            self.fields[name].choices = [c for c in self.fields[name].choices if c[0]]  # drop the blank "-----"
        if user is not None:
            # The email always comes from the signed-in account, so applications show in the right portal.
            self.fields["email"].initial = user.email
            self.fields["email"].disabled = True
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def clean_student_number(self):
        return self.cleaned_data.get("student_number", "").strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("past_student_choice") == "yes" and not cleaned.get("student_number"):
            self.add_error("student_number", "Please enter your MSVA student number.")
        track = cleaned.get("track")
        if self.user is not None and track is not None:
            if Application.objects.filter(user=self.user, track=track).exists():
                raise forms.ValidationError(
                    f"You have already applied for {track.title}. You can follow its status on your dashboard.")
        return cleaned

    def save(self, commit=True):
        application = super().save(commit=False)
        application.past_student = self.cleaned_data["past_student_choice"] == "yes"
        application.needs_placement_support = self.cleaned_data["placement_choice"] == "yes"
        application.terms_accepted_at = timezone.now()
        if not application.past_student:
            application.student_number = ""
        if self.user is not None:
            application.user = self.user
            application.email = self.user.email
        if commit:
            application.save()
        return application
