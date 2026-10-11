# CareLink API

This is the backend for a small healthcare app. Users can sign up, log in, and manage patients and doctors, and then assign doctors to patients. It's built with Django, Django REST Framework and PostgreSQL, and uses JWT for authentication.

I wanted the rules to be simple to explain: you own the patients you create, doctors live in a shared directory that everyone can read, and a mapping connects one patient to one doctor.

## What it does

The assignment asked for registration and login, CRUD for patients and doctors, and patient-doctor mappings. All of that is in. While building it I added a few things I thought a real app would need:

- Logout that actually invalidates the refresh token, plus a profile endpoint and change-password
- Search, filtering and ordering on the list endpoints
- Optional pagination (add `?page=1`; without it you get a plain array)
- A "primary doctor" flag and notes on each mapping
- A doctor availability flag, so unavailable doctors can't be assigned
- A small `/api/stats/` endpoint
- Swagger docs at `/api/docs/`
- Rate limiting on register and login
- A Postman collection and 38 automated tests

## Stack

Python 3.10+, Django 5, DRF, `djangorestframework-simplejwt`, PostgreSQL, `django-filter`, `drf-spectacular` for the docs, and `python-decouple` for reading the `.env` file.

## Project layout

```
carelink_backend/
├── config/      settings, urls, test settings
├── core/        shared bits: mixins, pagination, error handler, validators, stats view
├── accounts/    register, login, logout, profile, change password
├── patients/    model, serializer, filters, views
├── doctors/     model, serializer, filters, permissions, views
├── mappings/    model, serializers, views
├── docs/        API reference and database notes
└── postman/     Postman collection
```

Every app is laid out the same way (models, serializers, views, urls, tests), so it's easy to find things.

## Setup

You need Python 3.10+ and PostgreSQL running locally.

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # on Windows: Copy-Item .env.example .env
```

Open `.env` and fill in your database details, then create the database and run the server:

```bash
psql -U postgres -c "CREATE DATABASE carelink_db;"
python manage.py migrate
python manage.py runserver
```

The API is at `http://127.0.0.1:8000/api/` and the Swagger page is at `http://127.0.0.1:8000/api/docs/`. If you want to use the admin panel, run `python manage.py createsuperuser` first.

### Environment variables

| Variable | Required | Default | What it's for |
|---|---|---|---|
| `SECRET_KEY` | yes | | Django secret key |
| `DEBUG` | no | `False` | Set to `True` for local development only |
| `ALLOWED_HOSTS` | no | `localhost,127.0.0.1` | Comma-separated list |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | yes | | PostgreSQL credentials |
| `DB_HOST`, `DB_PORT` | no | `localhost`, `5432` | Where PostgreSQL is running |
| `ACCESS_TOKEN_MINUTES` | no | `30` | Access token lifetime |
| `REFRESH_TOKEN_DAYS` | no | `7` | Refresh token lifetime |
| `AUTH_THROTTLE_RATE` | no | `10/min` | Rate limit on register and login |
| `LOG_LEVEL` | no | `INFO` | Log level |

To generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## Running the tests

The tests run on in-memory SQLite, so you don't need PostgreSQL for them:

```bash
python manage.py test --settings=config.test_settings
```

They cover auth, validation, who can see or change what, filtering, pagination, the mapping rules and the stats endpoint. If you don't have a `.env` file, set `SECRET_KEY`, `DB_NAME`, `DB_USER` and `DB_PASSWORD` to any value first (the tests never connect to them).

## Trying it out

The easiest way is Postman. Import `postman/CareLink.postman_collection.json`, run Register, then Login. Login saves the token for you, so the other requests work straight away. Creating a patient, doctor or mapping also saves its id for the follow-up requests.

You can also use Swagger: open `/api/docs/`, click Authorize and paste in the access token.

From a terminal with curl:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"Str0ng!Pass123"}'

curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Str0ng!Pass123"}'

curl http://127.0.0.1:8000/api/patients/ -H "Authorization: Bearer <access_token>"
```

## Endpoints

Request and response examples for each of these are in [`docs/API.md`](docs/API.md).

| Method and path | What it does |
|---|---|
| `POST /api/auth/register/` | Create an account |
| `POST /api/auth/login/` | Get access and refresh tokens |
| `POST /api/auth/logout/` | Blacklist a refresh token |
| `POST /api/auth/token/refresh/` | Get a new access token |
| `GET`, `PATCH /api/auth/me/` | View or update your profile |
| `POST /api/auth/change-password/` | Change your password |
| `POST`, `GET /api/patients/` | Add a patient / list your patients |
| `GET`, `PUT`, `PATCH`, `DELETE /api/patients/<id>/` | Read, update or delete a patient |
| `POST`, `GET /api/doctors/` | Add a doctor / list all doctors |
| `GET`, `PUT`, `PATCH`, `DELETE /api/doctors/<id>/` | Read, update or delete a doctor |
| `POST`, `GET /api/mappings/` | Assign a doctor / list mappings |
| `GET /api/mappings/<patient_id>/` | Doctors assigned to one patient |
| `PATCH`, `DELETE /api/mappings/<id>/` | Edit notes or primary flag / remove a mapping |
| `GET /api/stats/` | Some summary numbers |

## Decisions worth explaining

**Patients are private to whoever created them.** This is medical data, so I scoped patients, and the mappings that show who treats them, to the user who made them. If you ask for someone else's patient you get a 404 instead of a 403, so the API never confirms that the record exists.

**Doctors are shared.** Any logged-in user can see and assign any doctor, but only the person who added a doctor can edit or delete it.

**Email is the username.** I used Django's built-in `User` model and store the email as the username. Emails are lowercased and compared case-insensitively. A custom user model would be cleaner for a bigger project, but it felt like too much for this scope.

**Rules are checked twice.** Something like "a patient can only have one primary doctor" is validated in the serializer so the error message is clear, and also enforced by a database constraint in case two requests arrive at the same time.

**Pagination is optional.** The assignment says "retrieve all", so the lists return plain arrays by default. Adding `?page=1` switches to the usual `count / next / previous / results` format.

**One URL, two meanings.** The assignment has `GET /api/mappings/<patient_id>/` and `DELETE /api/mappings/<id>/`, which look identical. I kept both as specified: GET treats the number as a patient id, while PATCH and DELETE treat it as a mapping id. It works, but it's the part of the design I like least, and I'd probably change it to `/api/patients/<id>/doctors/` in a real project.

**Same error format everywhere.** Every error looks like `{"status_code", "message", "errors"}`, which keeps things easy for a frontend to handle.

## Known limitations

- No roles. Every user is treated the same, so there's no admin, doctor or receptionist role yet.
- Deleting a patient is permanent. There's no soft delete or audit trail, which a real medical system would need.
- It hasn't been deployed anywhere. For production you'd also want `gunicorn`, `whitenoise` for static files, and `DEBUG=False`.

## Ideas for later

- Appointments between patients and doctors
- Role-based permissions
- Soft deletes and an audit log
- Docker Compose and a CI pipeline that runs the tests

---

Built by Ayush Srivastava. Questions or feedback: ayushwww4@gmail.com