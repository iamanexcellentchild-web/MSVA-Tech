import secrets

from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation

from .models import Profile

User = get_user_model()


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autocomplete": "given-name"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autocomplete": "family-name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}))
    password1 = forms.CharField(label="Password", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
                                help_text="At least 8 characters; not too common or all numbers.")
    password2 = forms.CharField(label="Confirm password", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Sign in instead.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords don't match.")
        elif p1:
            candidate = User(email=cleaned.get("email", ""), first_name=cleaned.get("first_name", ""),
                             last_name=cleaned.get("last_name", ""))
            try:
                password_validation.validate_password(p1, candidate)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        email = self.cleaned_data["email"]
        username = email[:150]
        if User.objects.filter(username=username).exists():
            username = f"{email.split('@')[0][:120]}-{secrets.token_hex(4)}"
        user = User.objects.create_user(
            username=username, email=email, password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"], last_name=self.cleaned_data["last_name"],
        )
        Profile.objects.get_or_create(user=user)
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}))
    password = forms.CharField(strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    error_message = "Incorrect email or password."

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email, password = cleaned.get("email"), cleaned.get("password")
        if email and password:
            account = User.objects.filter(email__iexact=email).first()
            if account is not None and not account.has_usable_password():
                raise forms.ValidationError(
                    "This account uses Google sign-in. Continue with Google, "
                    "then set a password on your profile page if you'd like one."
                )
            user = authenticate(self.request, username=account.username if account else email, password=password)
            if user is None:
                raise forms.ValidationError(self.error_message)
            if not user.is_active:
                raise forms.ValidationError("This account has been disabled.")
            self.user = user
        return cleaned


class UserDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["photo", "phone", "country", "city", "bio"]
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+234 800 000 0000"}),
            "country": forms.TextInput(attrs={"placeholder": "e.g. Nigeria"}),
            "city": forms.TextInput(attrs={"placeholder": "e.g. Lagos"}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "A few words about you..."}),
            "photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {"bio": "About me"}
        help_texts = {"photo": ""}
