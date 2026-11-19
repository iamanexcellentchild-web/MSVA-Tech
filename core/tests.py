import shutil
import tempfile
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.tokens import issue_tokens
from core.models import Application, Stat, Track

User = get_user_model()
TEST_MEDIA = tempfile.mkdtemp(prefix="msva-test-media-")


def tearDownModule():
    shutil.rmtree(TEST_MEDIA, ignore_errors=True)


def login_with_jwt(client, user):
    access, refresh = issue_tokens(user)
    client.cookies[settings.JWT_AUTH_COOKIE] = access
    client.cookies[settings.JWT_REFRESH_COOKIE] = refresh
    return access, refresh


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MEDIA_ROOT=TEST_MEDIA)
class SiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_academy", verbosity=0)
        cls.user = User.objects.create_user("ada@example.com", "ada@example.com", first_name="Ada", last_name="L")
        cls.track = Track.objects.get(slug="cybersecurity")

    def test_public_pages_render(self):
        for name in ["home", "about", "track_list", "benefits", "team", "contact"]:
            resp = self.client.get(reverse(f"core:{name}"))
            self.assertEqual(resp.status_code, 200, name)
        self.assertContains(self.client.get(reverse("accounts:login")), "Sign in", status_code=200)

    def test_every_track_has_its_own_page(self):
        for track in Track.objects.all():
            resp = self.client.get(track.get_absolute_url())
            self.assertContains(resp, track.title.upper())
            self.assertContains(resp, "WEEK-BY-WEEK SYLLABUS")

    def test_syllabus_image_shown_under_track(self):
        self.track.syllabus_image = "tracks/syllabus/demo.png"
        self.track.save()
        resp = self.client.get(self.track.get_absolute_url())
        self.assertContains(resp, "/media/tracks/syllabus/demo.png")

    def test_apply_requires_login(self):
        resp = self.client.get(reverse("core:apply"))
        self.assertRedirects(resp, f"{reverse('accounts:login')}?next=/apply/", fetch_redirect_response=False)

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(resp.status_code, 302)

    def test_apply_embeds_google_form(self):
        login_with_jwt(self.client, self.user)
        resp = self.client.get(reverse("core:apply_track", args=[self.track.slug]))
        self.assertContains(resp, settings.ACADEMY["apply_form_embed_url"])
        self.assertContains(resp, reverse("core:apply_thanks"))

    def test_thanks_page_shows_chosen_track(self):
        login_with_jwt(self.client, self.user)
        self.client.get(reverse("core:apply_track", args=[self.track.slug]))
        thanks = self.client.get(reverse("core:apply_thanks"))
        self.assertContains(thanks, "Thanks for filling the form")
        self.assertContains(thanks, "you will be contacted")
        self.assertContains(thanks, "Cybersecurity")

    def test_contact_form(self):
        resp = self.client.post(reverse("core:contact"), {
            "name": "Bola", "email": "bola@example.com", "subject": "Hi", "message": "Question about tracks"})
        self.assertRedirects(resp, reverse("core:contact"))


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ada@example.com", "ada@example.com")

    def test_expired_access_is_refreshed_from_refresh_cookie(self):
        _, refresh = issue_tokens(self.user)
        self.client.cookies[settings.JWT_REFRESH_COOKIE] = refresh
        resp = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(settings.JWT_AUTH_COOKIE, resp.cookies)

    def test_invalid_cookies_are_cleared(self):
        self.client.cookies[settings.JWT_AUTH_COOKIE] = "garbage"
        resp = self.client.get(reverse("core:home"))
        self.assertEqual(resp.cookies[settings.JWT_AUTH_COOKIE].value, "")

    def test_logout_blacklists_refresh_token(self):
        _, refresh = login_with_jwt(self.client, self.user)
        self.client.post(reverse("accounts:logout"))
        self.client.cookies.clear()
        self.client.cookies[settings.JWT_REFRESH_COOKIE] = refresh
        self.assertEqual(self.client.get(reverse("accounts:dashboard")).status_code, 302)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="cid", GOOGLE_OAUTH_CLIENT_SECRET="secret")
    def test_google_oauth_flow(self):
        resp = self.client.get(reverse("accounts:google_login") + "?next=/apply/")
        self.assertTrue(resp["Location"].startswith("https://accounts.google.com/"))
        state = self.client.session["google_oauth"]["state"]
        nonce = self.client.session["google_oauth"]["nonce"]

        claims = {"sub": "g-123", "email": "new@example.com", "email_verified": True,
                  "given_name": "New", "family_name": "Student", "picture": "https://x/y.png", "nonce": nonce}
        with mock.patch("accounts.google.exchange_code", return_value="idtok"), \
             mock.patch("accounts.google.google_id_token.verify_oauth2_token", return_value=claims):
            resp = self.client.get(reverse("accounts:google_callback"), {"code": "abc", "state": state})

        self.assertRedirects(resp, "/apply/", fetch_redirect_response=False)
        self.assertIn(settings.JWT_AUTH_COOKIE, resp.cookies)
        self.assertTrue(resp.cookies[settings.JWT_AUTH_COOKIE]["httponly"])
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.profile.google_sub, "g-123")

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="cid", GOOGLE_OAUTH_CLIENT_SECRET="secret")
    def test_google_callback_rejects_bad_state(self):
        self.client.get(reverse("accounts:google_login"))
        resp = self.client.get(reverse("accounts:google_callback"), {"code": "abc", "state": "forged"})
        self.assertRedirects(resp, reverse("accounts:login"), fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="cid", GOOGLE_OAUTH_CLIENT_SECRET="secret")
    def test_api_google_login_and_me(self):
        claims = {"sub": "g-9", "email": "api@example.com", "email_verified": True, "given_name": "Api"}
        with mock.patch("accounts.google.google_id_token.verify_oauth2_token", return_value=claims):
            resp = self.client.post("/api/auth/google/", {"id_token": "tok"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        access = resp.json()["access"]
        me = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(me.json()["email"], "api@example.com")

    def test_api_tracks_public(self):
        call_command("seed_academy", verbosity=0)
        self.assertEqual(len(self.client.get("/api/tracks/").json()), 8)
        detail = self.client.get("/api/tracks/data-analysis/").json()
        self.assertEqual(len(detail["weeks"]), 6)

    def test_refresh_endpoint_rotates(self):
        refresh = str(RefreshToken.for_user(self.user))
        resp = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class EmailAuthTests(TestCase):
    def test_signup_logs_in_and_redirects(self):
        resp = self.client.post(reverse("accounts:signup"), {
            "first_name": "Bola", "last_name": "Ade", "email": "Bola@Example.com",
            "password1": "s3cure-Passw0rd", "password2": "s3cure-Passw0rd", "next": "/apply/"})
        self.assertRedirects(resp, "/apply/", fetch_redirect_response=False)
        self.assertIn(settings.JWT_AUTH_COOKIE, resp.cookies)
        user = User.objects.get(email="bola@example.com")
        self.assertTrue(user.check_password("s3cure-Passw0rd"))

    def test_signup_rejects_duplicate_email_and_mismatched_passwords(self):
        User.objects.create_user("bola@example.com", "bola@example.com", "x")
        resp = self.client.post(reverse("accounts:signup"), {
            "first_name": "B", "last_name": "A", "email": "bola@example.com",
            "password1": "s3cure-Passw0rd", "password2": "different-Passw0rd"})
        self.assertContains(resp, "already exists")
        self.assertContains(resp, "don&#x27;t match")

    def test_login_with_email_and_password(self):
        User.objects.create_user("bola@example.com", "bola@example.com", "s3cure-Passw0rd")
        bad = self.client.post(reverse("accounts:login"), {"email": "bola@example.com", "password": "nope"})
        self.assertContains(bad, "Incorrect email or password")
        ok = self.client.post(reverse("accounts:login"), {"email": "BOLA@example.com", "password": "s3cure-Passw0rd"})
        self.assertRedirects(ok, "/dashboard/", fetch_redirect_response=False)

    def test_google_only_account_is_told_to_use_google(self):
        user = User(username="g@example.com", email="g@example.com")
        user.set_unusable_password()
        user.save()
        resp = self.client.post(reverse("accounts:login"), {"email": "g@example.com", "password": "whatever1"})
        self.assertContains(resp, "uses Google sign-in")

    def test_profile_update_and_password_change(self):
        user = User.objects.create_user("bola@example.com", "bola@example.com", "s3cure-Passw0rd")
        login_with_jwt(self.client, user)
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        resp = self.client.post(reverse("accounts:profile"), {
            "action": "details", "first_name": "Bola", "last_name": "Ade",
            "phone": "+2348000000000", "country": "Nigeria", "city": "Lagos", "bio": "Hi"})
        self.assertRedirects(resp, reverse("accounts:profile"))
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Bola")
        self.assertEqual(user.profile.city, "Lagos")

        resp = self.client.post(reverse("accounts:profile"), {
            "action": "password", "old_password": "s3cure-Passw0rd",
            "new_password1": "an0ther-Passw0rd", "new_password2": "an0ther-Passw0rd"})
        self.assertRedirects(resp, "/profile/", fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.check_password("an0ther-Passw0rd"))

    def test_login_page_hides_google_when_not_configured(self):
        with override_settings(GOOGLE_OAUTH_CLIENT_ID="", GOOGLE_OAUTH_CLIENT_SECRET=""):
            resp = self.client.get(reverse("accounts:login"))
        self.assertNotContains(resp, "Continue with Google")
        self.assertNotContains(resp, "isn't configured")


class AuthAPITests(TestCase):
    def test_register_then_login_then_me(self):
        resp = self.client.post("/api/auth/register/", {
            "first_name": "Bola", "last_name": "Ade", "email": "bola@example.com",
            "password": "s3cure-Passw0rd"}, content_type="application/json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIn("access", resp.json())
        self.assertEqual(resp.json()["user"]["email"], "bola@example.com")

        dup = self.client.post("/api/auth/register/", {
            "first_name": "B", "last_name": "A", "email": "bola@example.com",
            "password": "s3cure-Passw0rd"}, content_type="application/json")
        self.assertEqual(dup.status_code, 400)
        self.assertIn("email", dup.json())

        weak = self.client.post("/api/auth/register/", {
            "first_name": "C", "last_name": "D", "email": "c@example.com", "password": "123"},
            content_type="application/json")
        self.assertEqual(weak.status_code, 400)
        self.assertIn("password", weak.json())

        bad = self.client.post("/api/auth/login/", {"email": "bola@example.com", "password": "wrong"},
                               content_type="application/json")
        self.assertEqual(bad.status_code, 401)

        ok = self.client.post("/api/auth/login/", {"email": "bola@example.com", "password": "s3cure-Passw0rd"},
                              content_type="application/json")
        self.assertEqual(ok.status_code, 200)
        me = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {ok.json()['access']}")
        self.assertEqual(me.json()["first_name"], "Bola")


class HealthzTests(TestCase):
    def test_healthz_makes_no_database_queries(self):
        with self.assertNumQueries(0):
            resp = self.client.get("/healthz/")
        self.assertEqual(resp.content, b"ok")

    @override_settings(ALLOWED_HOSTS=["example.com"], SECURE_SSL_REDIRECT=True)
    def test_healthz_ignores_unknown_host_and_https_redirect(self):
        resp = self.client.get("/healthz/", HTTP_HOST="10.0.0.5:10000")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class AdvisorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_academy", verbosity=0)

    def ask(self, **payload):
        return self.client.post("/api/advisor/", payload, content_type="application/json")

    def test_security_lover_gets_cybersecurity_first(self):
        resp = self.ask(interests=["protect", "logic"], goal="job", experience="some",
                        about="I want to become an ethical hacker and protect networks")
        self.assertEqual(resp.status_code, 200)
        recs = resp.json()["recommendations"]
        self.assertEqual(recs[0]["slug"], "cybersecurity")
        self.assertEqual(recs[0]["match"], 100)
        self.assertTrue(any("ethical" in r or "hacker" in r for r in recs[0]["reasons"]))
        self.assertLessEqual(len(recs), 3)

    def test_creative_freelancer_gets_design(self):
        recs = self.ask(interests=["design"], goal="freelance", experience="none",
                        about="I love drawing and want to design logos for small businesses").json()["recommendations"]
        self.assertEqual(recs[0]["slug"], "graphics-design")

    def test_phone_only_marketer_gets_digital_marketing(self):
        recs = self.ask(interests=["marketing"], goal="business", laptop=False).json()["recommendations"]
        self.assertEqual(recs[0]["slug"], "digital-marketing")
        self.assertTrue(any("smartphone" in r for r in recs[0]["reasons"]))

    def test_free_text_alone_works_and_bad_input_is_ignored(self):
        recs = self.ask(interests=["nonsense"], goal="??", about="excel spreadsheets and dashboards").json()["recommendations"]
        self.assertEqual(recs[0]["slug"], "data-analysis")

    def test_unpublished_tracks_are_never_recommended(self):
        Track.objects.filter(slug="cybersecurity").update(is_published=False)
        recs = self.ask(interests=["protect"], about="hacking").json()["recommendations"]
        self.assertNotIn("cybersecurity", [r["slug"] for r in recs])

    def test_home_page_has_logo_and_advisor(self):
        resp = self.client.get("/")
        self.assertContains(resp, "images/logo-mark")
        self.assertContains(resp, 'id="advisorPanel"')
        self.assertContains(resp, "data-open-advisor")

    def test_track_page_lists_every_other_track(self):
        resp = self.client.get(Track.objects.get(slug="cybersecurity").get_absolute_url())
        self.assertEqual(resp.content.decode().count('class="track-mini"'), Track.objects.count() - 1)

    def test_track_photos_show_on_cards(self):
        resp = self.client.get("/tracks/")
        self.assertContains(resp, "images/tracks/cybersecurity")
        recs = self.ask(interests=["data"]).json()["recommendations"]
        self.assertIn("images/tracks/", recs[0]["image"])

    def test_home_stats_show_real_numbers_not_zero(self):
        html = self.client.get("/").content.decode()
        for stat in Stat.objects.all():
            self.assertIn(f"{stat.value:,}{stat.suffix}", html)
        self.assertNotIn(">0</strong>", html)
