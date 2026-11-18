# MS. Virtual Academy: Django site

Multi-page, server-rendered version of the academy website, with Google sign-in (OAuth 2.0 + JWT),
an application form with email confirmation, and a student dashboard.

## Quick start

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # then fill in the values (see below)
python manage.py migrate
python manage.py seed_academy    # loads tracks, syllabus, stats, benefits, team, FAQs
python manage.py createsuperuser # for the admin at /admin/
python manage.py runserver
```

## Pages

| URL | Page |
| --- | --- |
| `/` | Home (hero, impact stats, tracks, benefits) |
| `/about/` | About, mission, how it works, team, FAQs |
| `/tracks/` | All tracks |
| `/tracks/<slug>/` | One page per track: overview, outcomes, week-by-week syllabus, **syllabus image**, tools, careers, FAQs |
| `/apply/` and `/tracks/<slug>/apply/` | Embedded Google Form (requires Google sign-in); redirects to the thank-you page on submit |
| `/apply/thank-you/` | Thank-you page shown after submitting |
| `/dashboard/` | Student dashboard: name, courses applied for, status, next steps |
| `/benefits/`, `/team/`, `/contact/` | Benefits, team, contact form |
| `/accounts/login/` | "Continue with Google" |
| `/admin/` | Manage all content and review applications |

## Adding a syllabus image to a track

Go to **Admin → Tracks → (track) → Images**, upload a **Syllabus image** and, optionally, a caption.
It appears under the week-by-week syllabus on that track's page. You can also upload a **Cover image**
for the track card and page banner. Week topics, outcomes, tools and so on can all be edited in the same screen.

## Authentication (Google OAuth + JWT)

1. Google redirects back to `/accounts/google/callback/`. The server checks `state` and `nonce`,
   exchanges the code, and verifies the Google ID token's signature, audience and expiry.
2. The user is found or created, and a Simple JWT **access/refresh pair** is issued.
3. Both tokens are stored in **HttpOnly cookies**. `accounts.middleware.JWTCookieMiddleware` reads them
   on every page request, and refreshes the access token from the refresh token when it expires.
4. Signing out blacklists the refresh token.

**Google Cloud setup:** in [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials),
create an **OAuth client ID** (Web application). Add the authorized redirect URI
`http://localhost:8000/accounts/google/callback/` (and your production URL later), then put the
client ID and secret in `.env`.

### JSON API (for mobile apps or other clients)

| Method | Endpoint | Notes |
| --- | --- | --- |
| POST | `/api/auth/register/` | `{"first_name", "last_name", "email", "password"}` → 201 `{access, refresh, user}` |
| POST | `/api/auth/login/` | `{"email", "password"}` → `{access, refresh, user}` (401 if wrong) |
| POST | `/api/auth/google/` | `{"id_token": "<Google ID token>"}` → `{access, refresh, user}` |
| POST | `/api/auth/token/refresh/` | `{"refresh": "..."}` → new pair (rotated) |
| POST | `/api/auth/logout/` | `{"refresh": "..."}` blacklists it |
| GET | `/api/auth/me/` | `Authorization: Bearer <access>` |
| GET | `/api/tracks/`, `/api/tracks/<slug>/` | Public |
| GET | `/api/me/applications/` | Authenticated |

## Email (Gmail SMTP, free tier)

After someone submits the application form, they get a confirmation email: "If you are shortlisted, you will be contacted".

1. Turn on **2-Step Verification** on the academy's Gmail account.
2. Create an **App Password** at <https://myaccount.google.com/apppasswords>.
3. Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` (the 16-character app password) in `.env`.

Until those are set, emails are printed to the terminal running `runserver`. If sending fails, the
application is still saved; **Admin → Applications** shows a "confirmation email sent" column.

## Tests

```bash
python manage.py test
```

The original static files are kept in `legacy/` for reference.

## Deployment (free): Netlify → Render (Django) → Neon (Postgres)

Netlify can't run Python, so it only forwards requests (`netlify.toml`) to the Django app on Render.
Data lives in Neon; uploads go to Cloudinary when `CLOUDINARY_URL` is set.

1. **Neon:** create a project and copy the connection string (`postgresql://...?sslmode=require`).
2. **Load data once, from your PC:** put that string in `.env` as `DATABASE_URL`, then run
   `python manage.py migrate`, `python manage.py seed_academy` and `python manage.py createsuperuser`.
   Remove `DATABASE_URL` from `.env` afterwards to go back to local SQLite.
3. **Cloudinary (recommended):** copy the `CLOUDINARY_URL` from the dashboard.
4. **Render:** push this repo to GitHub, choose **New → Blueprint** and pick the repo (`render.yaml`). Set:
   - `DJANGO_ALLOWED_HOSTS` = `msva.onrender.com,yoursite.netlify.app` (plus your domain)
   - `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://yoursite.netlify.app` (plus `https://yourdomain.com`)
   - `DATABASE_URL`, `CLOUDINARY_URL`, the Google keys, and
     `GOOGLE_OAUTH_REDIRECT_URI` = `https://yoursite.netlify.app/accounts/google/callback/`
5. **Netlify:** put your Render URL in `netlify.toml`, then connect the same repo to your Netlify site.
6. **Google Cloud:** add the step 4 redirect URI to the OAuth client.
7. **Keep it awake:** Render's free plan sleeps after 15 idle minutes and takes ~1 minute to wake, which
   can make Netlify time out. Use a free pinger (e.g. cron-job.org) to open `/healthz/` every 10 minutes. Ping only `/healthz/`:
   it never queries the database, so Neon can still pause and stay within its free 100 compute-hours.
