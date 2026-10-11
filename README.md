# CareLink API

A secure REST backend for managing patients, doctors and the care relationships between them.
Built with **Django**, **Django REST Framework**, **PostgreSQL** and **JWT authentication**.

CareLink is organised around one simple idea: *a user owns the patients they create, doctors form a shared
directory, and mappings connect the two with a few sensible business rules on top.*

---

## Features

**Core (assignment requirements)**
- Register / log in with email and password, JWT access + refresh tokens (`djangorestframework-simplejwt`)
- Full CRUD for patients and doctors
- Patient-doctor mappings: assign, list, look up by patient, remove
- PostgreSQL via the Django ORM, secrets in environment variables
- Validation and consistent error handling on every endpoint

**Beyond the brief**
- **Logout with token blacklisting**, plus profile (`/me/`) and change-password endpoints
- **Search, filtering and ordering** on patients, doctors and mappings
- **Opt-in pagination** (`?page=N`), so the plain list responses stay simple arrays
- **Primary doctor** per patient and free-text **care notes** on each mapping
- **Doctor availability**: unavailable doctors cannot receive new patients
- **Dashboard stats** endpoint (patients without a doctor, doctors by specialization, ...)
- **Interactive API docs** (Swagger UI) generated from the code
- **Rate limiting** on register / login
- **One uniform error format** across the whole API
- Ready-made **Postman collection** and a **38-test** automated suite

---

## Tech stack

| Layer | Choice |
|---|---|
| Language / framework | Python 3.10+, Django 5, Django REST Framework |
| Auth | JWT via `djangorestframework-simplejwt` (with token blacklist) |
| Database | PostgreSQL (SQLite only for the test-suite) |
| Filtering | `django-filter` + DRF search / ordering |
| API docs | `drf-spectacular` (OpenAPI 3 + Swagger UI) |
| Config | `python-decouple` (`.env` file) |

---

## Project structure

```
carelink_backend/
├── config/            # settings, root URLs, wsgi/asgi, test settings
├── core/              # shared building blocks
│   ├── mixins.py        # ownership scoping + created_by stamping
│   ├── pagination.py    # opt-in pagination
│   ├── exceptions.py    # uniform error format
│   ├── validators.py    # phone number validator
│   ├── views.py         # /api/stats/
│   └── test_utils.py    # test helpers
├── accounts/          # register, login, logout, profile, change password
├── patients/          # Patient model, serializer, filters, views
├── doctors/           # Doctor model, serializer, filters, permissions, views
├── mappings/          # PatientDoctorMapping model, rules, views
├── docs/              # API reference and database design
├── postman/           # importable Postman collection
├── requirements.txt
└── .env.example
```

Each app follows the same layout (`models → serializers → views → urls → tests`), so finding where
something lives is predictable.

---

## Getting started

### 1. Prerequisites
- Python 3.10 or newer
- PostgreSQL 13 or newer running locally

### 2. Install
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
```
Edit `.env` (see the table below), then create the database:
```bash
psql -U postgres -c "CREATE DATABASE carelink_db;"
```

### 4. Migrate and run
```bash
python manage.py migrate
python manage.py createsuperuser     # optional, for /admin/
python manage.py runserver
```

The API is now at `http://127.0.0.1:8000/api/` and the interactive docs at
`http://127.0.0.1:8000/api/docs/`.

### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | yes | - | Django secret key |
| `DEBUG` | no | `False` | Debug mode (use `True` locally only) |
| `ALLOWED_HOSTS` | no | `localhost,127.0.0.1` | Comma-separated host list |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | yes | - | PostgreSQL credentials |
| `DB_HOST` / `DB_PORT` | no | `localhost` / `5432` | PostgreSQL location |
| `ACCESS_TOKEN_MINUTES` | no | `30` | Access token lifetime |
| `REFRESH_TOKEN_DAYS` | no | `7` | Refresh token lifetime |
| `AUTH_THROTTLE_RATE` | no | `10/min` | Rate limit for register / login |
| `LOG_LEVEL` | no | `INFO` | Application log level |

Generate a strong secret key with:
```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

---

## Running the tests

The suite runs on in-memory SQLite, so no PostgreSQL server is needed:

```bash
python manage.py test --settings=config.test_settings
```

It covers authentication, validation, ownership rules, permissions, filtering, pagination, mapping
business rules and the stats endpoint.

---

## Trying the API

**Swagger UI:** open `/api/docs/`, click *Authorize* and paste the access token.

**Postman:** import `postman/CareLink.postman_collection.json`. Run *Register*, then *Login*; the login
request stores the tokens in collection variables, so every other request is authenticated
automatically. Creating a patient / doctor / mapping also stores its id for the follow-up requests.

**curl:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"Str0ng!Pass123"}'

curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Str0ng!Pass123"}'

curl http://127.0.0.1:8000/api/patients/ -H "Authorization: Bearer <access_token>"
```

---

## Endpoint overview

Full request / response examples live in [`docs/API.md`](docs/API.md).

| Area | Method & path | Description |
|---|---|---|
| Auth | `POST /api/auth/register/` | Create an account |
| | `POST /api/auth/login/` | Get access + refresh tokens |
| | `POST /api/auth/logout/` | Blacklist a refresh token |
| | `POST /api/auth/token/refresh/` | Exchange a refresh token for a new access token |
| | `GET` `PATCH /api/auth/me/` | View / update your profile |
| | `POST /api/auth/change-password/` | Change your password |
| Patients | `POST` `GET /api/patients/` | Create / list your patients |
| | `GET` `PUT` `PATCH` `DELETE /api/patients/<id>/` | Read / update / delete a patient |
| Doctors | `POST` `GET /api/doctors/` | Create / list all doctors |
| | `GET` `PUT` `PATCH` `DELETE /api/doctors/<id>/` | Read / update / delete a doctor |
| Mappings | `POST` `GET /api/mappings/` | Assign a doctor / list mappings |
| | `GET /api/mappings/<patient_id>/` | Doctors assigned to a patient |
| | `PATCH` `DELETE /api/mappings/<id>/` | Update notes / primary flag, or remove a mapping |
| Insights | `GET /api/stats/` | Dashboard numbers |
| Docs | `GET /api/docs/`, `/api/schema/` | Swagger UI and OpenAPI schema |

---

## Design decisions

- **Ownership by default.** Patient data is medical data, so patients (and the mappings that reveal who treats
  them) are scoped to the user who created them. Requests for someone else's record return `404`, not `403`,
  so the API never confirms that a record exists.
- **Doctors are a shared directory.** Any signed-in user can read and assign any doctor, but only the user who
  added a doctor can edit or delete it.
- **Email is the username.** Login uses the same address used at registration; emails are normalised to
  lowercase and compared case-insensitively.
- **Business rules in serializers.** Rules such as "one primary doctor per patient" are validated in the
  serializer for clear error messages *and* backed by a database constraint so they hold under concurrency.
- **Pagination is opt-in.** Lists return plain arrays by default; add `?page=1` (and optionally `&page_size=`)
  to get `{count, next, previous, results}`.
- **One URL, three jobs.** The brief specifies `GET /api/mappings/<patient_id>/` and
  `DELETE /api/mappings/<id>/`. They share a URL shape, so `GET` interprets the number as a patient id while
  `PATCH` / `DELETE` interpret it as a mapping id.
- **Uniform errors.** Every error returns `{"status_code", "message", "errors"}`, which keeps client-side
  handling simple.

---

## Possible next steps

- Appointments between a patient and a doctor
- Role-based access (admin / doctor / receptionist)
- Soft deletes and an audit trail for patient records
- Docker Compose setup and a CI pipeline running the test-suite
