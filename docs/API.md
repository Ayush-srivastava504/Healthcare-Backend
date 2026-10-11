# CareLink API Reference

Base URL (local): `http://127.0.0.1:8000`

All request and response bodies are JSON. Protected endpoints need:

```
Authorization: Bearer <access_token>
```

## Contents
- [Conventions](#conventions)
- [Authentication](#authentication)
- [Patients](#patients)
- [Doctors](#doctors)
- [Mappings](#mappings)
- [Stats](#stats)

---

## Conventions

### Error format
Every error uses the same shape:

```json
{
  "status_code": 400,
  "message": "Validation failed.",
  "errors": { "email": ["A user with this email already exists."] }
}
```

`errors` is only filled for validation failures (`400`); for other errors it is `null`.

| Status | Meaning |
|---|---|
| `200` / `201` / `204` | Success / created / deleted |
| `400` | Validation failed |
| `401` | Missing, invalid or expired token |
| `403` | Authenticated but not allowed (e.g. editing a doctor you did not create) |
| `404` | Not found (also returned for records owned by other users) |
| `409` | Database conflict |
| `429` | Throttled (register / login) |

### Pagination
Lists return a plain array. Add `?page=N` to opt in:

```
GET /api/patients/?page=2&page_size=5
```
```json
{ "count": 12, "next": "http://.../?page=3&page_size=5", "previous": "http://.../?page=1&page_size=5", "results": [ ... ] }
```
`page_size` defaults to 10, maximum 100.

### Search and ordering
`?search=<text>` and `?ordering=<field>` (prefix with `-` for descending) are available on list endpoints;
the searchable / orderable fields are listed per resource below.

---

## Authentication

### Register
`POST /api/auth/register/` (public, throttled)

```json
{ "name": "Alice", "email": "alice@example.com", "password": "Str0ng!Pass123" }
```
`201 Created`
```json
{ "id": 1, "name": "Alice", "email": "alice@example.com" }
```
Rules: valid email, unique (case-insensitive), password must pass Django's password validators.

### Login
`POST /api/auth/login/` (public, throttled)

```json
{ "email": "alice@example.com", "password": "Str0ng!Pass123" }
```
`200 OK`
```json
{
  "user": { "id": 1, "name": "Alice", "email": "alice@example.com" },
  "access": "<jwt access token>",
  "refresh": "<jwt refresh token>"
}
```

### Refresh token
`POST /api/auth/token/refresh/`
```json
{ "refresh": "<jwt refresh token>" }
```
Returns a new `access` token (and a rotated `refresh` token; the old one is blacklisted).

### Logout
`POST /api/auth/logout/` (authenticated)
```json
{ "refresh": "<jwt refresh token>" }
```
`204 No Content`. The refresh token can no longer be used.

### Profile
`GET /api/auth/me/` returns the current user. `PATCH /api/auth/me/` updates the name:
```json
{ "name": "Alice B" }
```
```json
{ "id": 1, "name": "Alice B", "email": "alice@example.com", "date_joined": "2026-10-10T12:00:00Z" }
```
The email cannot be changed.

### Change password
`POST /api/auth/change-password/`
```json
{ "old_password": "Str0ng!Pass123", "new_password": "An0ther!Pass987" }
```
`200 OK` -> `{ "message": "Password updated." }`

---

## Patients

Patients belong to the user who created them; you only ever see your own.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | read-only |
| `name` | string | required, max 150 |
| `age` | integer | required, 0-130 |
| `gender` | string | required: `M`, `F`, `O` |
| `blood_group` | string | optional: `A+ A- B+ B- AB+ AB- O+ O-` |
| `phone` | string | optional, 7-20 chars: digits, spaces, dashes, optional leading `+` |
| `address` | string | optional |
| `medical_history` | string | optional |
| `created_by` | integer | read-only, the owner's user id |
| `created_at` / `updated_at` | datetime | read-only |

### Create
`POST /api/patients/`
```json
{
  "name": "John Doe",
  "age": 40,
  "gender": "M",
  "blood_group": "O+",
  "phone": "+40 721 000 111",
  "address": "12 Main Street",
  "medical_history": "Hypertension"
}
```
`201 Created` returns the full patient object.

### List
`GET /api/patients/`

| Query param | Example | Effect |
|---|---|---|
| `gender` | `?gender=F` | exact match |
| `blood_group` | `?blood_group=O%2B` | exact match |
| `min_age` / `max_age` | `?min_age=30&max_age=60` | age range |
| `search` | `?search=john` | matches name or phone |
| `ordering` | `?ordering=-age` | `name`, `age`, `created_at` |

### Retrieve / update / delete
- `GET /api/patients/<id>/`
- `PUT /api/patients/<id>/` (full update) or `PATCH` (partial)
- `DELETE /api/patients/<id>/` -> `204`

Deleting a patient also removes their mappings.

---

## Doctors

Doctors are a shared directory: everyone can read them, only the creator can modify or delete.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | read-only |
| `name` | string | required |
| `specialization` | string | required |
| `email` | string | required, unique (case-insensitive) |
| `phone` | string | optional, same format as patients |
| `experience_years` | integer | optional, default 0, max 70 |
| `is_available` | boolean | default `true`; unavailable doctors cannot be newly assigned |
| `created_by`, `created_at`, `updated_at` | | read-only |

### Create
`POST /api/doctors/`
```json
{
  "name": "Gregory House",
  "specialization": "Diagnostics",
  "email": "house@hospital.com",
  "phone": "+1 555 0100",
  "experience_years": 20
}
```

### List
`GET /api/doctors/`

| Query param | Example | Effect |
|---|---|---|
| `specialization` | `?specialization=cardio` | case-insensitive contains |
| `is_available` | `?is_available=true` | availability |
| `min_experience` | `?min_experience=10` | at least N years |
| `search` | `?search=house` | matches name or specialization |
| `ordering` | `?ordering=-experience_years` | `name`, `experience_years`, `created_at` |

### Retrieve / update / delete
- `GET /api/doctors/<id>/`
- `PUT` / `PATCH /api/doctors/<id>/` (creator only, otherwise `403`)
- `DELETE /api/doctors/<id>/` (creator only)

---

## Mappings

A mapping assigns a doctor to a patient. Rules:
- You can only assign doctors to **your own** patients.
- The same doctor cannot be assigned to the same patient twice.
- Unavailable doctors cannot be assigned.
- A patient can have at most **one primary doctor**.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | read-only |
| `patient` | integer | patient id (write on create) |
| `doctor` | integer | doctor id (write on create) |
| `is_primary` | boolean | default `false` |
| `notes` | string | optional care notes |
| `patient_name`, `doctor_name`, `doctor_specialization` | string | read-only convenience fields |
| `assigned_at` | datetime | read-only |

### Assign a doctor
`POST /api/mappings/`
```json
{ "patient": 1, "doctor": 3, "is_primary": true, "notes": "Lead physician" }
```
`201 Created`
```json
{
  "id": 7,
  "patient": 1,
  "patient_name": "John Doe",
  "doctor": 3,
  "doctor_name": "Gregory House",
  "doctor_specialization": "Diagnostics",
  "is_primary": true,
  "notes": "Lead physician",
  "assigned_at": "2026-10-10T12:00:00Z"
}
```

### List mappings
`GET /api/mappings/` returns mappings of your patients. Filters: `?patient=1`, `?doctor=3`, `?is_primary=true`,
`?search=<patient or doctor name>`, `?ordering=-assigned_at`.

### Doctors assigned to a patient
`GET /api/mappings/<patient_id>/` returns the mapping list for that patient (each item includes the doctor's
id, name and specialization). `404` if the patient is not yours.

### Update a mapping
`PATCH /api/mappings/<mapping_id>/` can change only `is_primary` and `notes`:
```json
{ "is_primary": true, "notes": "Moved to lead physician" }
```

### Remove a doctor from a patient
`DELETE /api/mappings/<mapping_id>/` -> `204 No Content`

---

## Stats

`GET /api/stats/`

```json
{
  "patients": { "total": 12, "without_doctor": 3 },
  "doctors": {
    "total": 8,
    "available": 7,
    "by_specialization": [
      { "specialization": "Cardiology", "total": 3 },
      { "specialization": "Neurology", "total": 2 }
    ]
  },
  "mappings": { "total": 15, "with_primary_doctor": 9 }
}
```
Patient and mapping figures cover your own data; doctor figures cover the shared directory.
