# CareLink API Reference

This is the reference for every endpoint in the API. When running locally the base URL is `http://127.0.0.1:8000`. Everything is JSON, both requests and responses.

Except for register, login and token refresh, every endpoint needs an access token in the header:

```
Authorization: Bearer <access_token>
```

If you'd rather click around than read this, the same endpoints are in Swagger at `/api/docs/` and in the Postman collection in the `postman/` folder.

**Contents:** [General notes](#general-notes) · [Authentication](#authentication) · [Patients](#patients) · [Doctors](#doctors) · [Mappings](#mappings) · [Stats](#stats)

---

## General notes

### Errors

All errors come back in the same shape, so a client only needs one way to handle them:

```json
{
  "status_code": 400,
  "message": "Validation failed.",
  "errors": { "email": ["A user with this email already exists."] }
}
```

`errors` is only filled in for validation problems (400). For anything else it's `null` and the `message` explains what happened.

| Status | When you'll see it |
|---|---|
| 200, 201, 204 | It worked (ok, created, deleted) |
| 400 | The data you sent didn't pass validation |
| 401 | The token is missing, invalid or expired |
| 403 | You're logged in but not allowed, e.g. editing a doctor someone else added |
| 404 | The record doesn't exist, or it belongs to another user |
| 409 | A database conflict |
| 429 | Too many register or login attempts |

A note on 404: I return it instead of 403 when you ask for someone else's patient, so the API doesn't reveal whether that record exists.

### Pagination

By default a list endpoint returns a plain array. If you want pages, add `?page=N`:

```
GET /api/patients/?page=2&page_size=5
```

```json
{
  "count": 12,
  "next": "http://.../?page=3&page_size=5",
  "previous": "http://.../?page=1&page_size=5",
  "results": [ ... ]
}
```

`page_size` defaults to 10 and can't go above 100.

### Search and ordering

List endpoints accept `?search=<text>` and `?ordering=<field>`. Put a `-` in front of the field to sort in descending order. The fields you can search and order by are listed under each resource below.

---

## Authentication

### Register

`POST /api/auth/register/` (public, rate limited)

```json
{ "name": "Alice", "email": "alice@example.com", "password": "Str0ng!Pass123" }
```

Response, `201 Created`:

```json
{ "id": 1, "name": "Alice", "email": "alice@example.com" }
```

The email has to be valid and not already taken (the check ignores case, and emails are stored in lowercase). The password has to pass Django's password validators, so very short, common or all-numeric passwords are rejected.

### Login

`POST /api/auth/login/` (public, rate limited)

```json
{ "email": "alice@example.com", "password": "Str0ng!Pass123" }
```

Response, `200 OK`:

```json
{
  "user": { "id": 1, "name": "Alice", "email": "alice@example.com" },
  "access": "<jwt access token>",
  "refresh": "<jwt refresh token>"
}
```

Use the `access` token in the `Authorization` header. It expires after 30 minutes by default. Keep the `refresh` token to get a new one.

### Refresh token

`POST /api/auth/token/refresh/`

```json
{ "refresh": "<jwt refresh token>" }
```

You get back a new `access` token and a new `refresh` token. The old refresh token is blacklisted, so always save the new one.

### Logout

`POST /api/auth/logout/` (needs a token)

```json
{ "refresh": "<jwt refresh token>" }
```

Returns `204 No Content`. After this the refresh token can't be used again. Access tokens can't be revoked, so the current one stays valid until it expires.

### Profile

`GET /api/auth/me/` returns the logged-in user. `PATCH /api/auth/me/` lets you change your name:

```json
{ "name": "Alice B" }
```

```json
{ "id": 1, "name": "Alice B", "email": "alice@example.com", "date_joined": "2026-10-10T12:00:00Z" }
```

The email can't be changed. If you send one it's ignored.

### Change password

`POST /api/auth/change-password/`

```json
{ "old_password": "Str0ng!Pass123", "new_password": "An0ther!Pass987" }
```

Returns `200 OK` with `{ "message": "Password updated." }`. The old password has to be correct, and the new one goes through the same validators as registration.

---

## Patients

Patients belong to whoever created them, and you only ever see your own.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | read-only |
| `name` | string | required, up to 150 characters |
| `age` | integer | required, 0 to 130 |
| `gender` | string | required: `M`, `F` or `O` |
| `blood_group` | string | optional: `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-` |
| `phone` | string | optional, 7 to 20 characters: digits, spaces, dashes, optional leading `+` |
| `address` | string | optional |
| `medical_history` | string | optional |
| `created_by` | integer | read-only, the id of the owner |
| `created_at`, `updated_at` | datetime | read-only |

### Create a patient

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

Returns `201 Created` with the saved patient.

### List patients

`GET /api/patients/` returns only your patients. You can narrow it down with these query parameters:

| Parameter | Example | What it does |
|---|---|---|
| `gender` | `?gender=F` | exact match |
| `blood_group` | `?blood_group=O%2B` | exact match (the `+` has to be URL-encoded as `%2B`) |
| `min_age`, `max_age` | `?min_age=30&max_age=60` | age range |
| `search` | `?search=john` | looks in name and phone |
| `ordering` | `?ordering=-age` | order by `name`, `age` or `created_at` |

### Get, update or delete one patient

- `GET /api/patients/<id>/`
- `PUT /api/patients/<id>/` replaces the record, so send all the required fields
- `PATCH /api/patients/<id>/` changes only the fields you send
- `DELETE /api/patients/<id>/` returns `204`

Deleting a patient also deletes their doctor assignments.

---

## Doctors

Doctors are a shared directory. Anyone who's logged in can read them, but only the user who added a doctor can edit or delete it.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | read-only |
| `name` | string | required |
| `specialization` | string | required |
| `email` | string | required, must be unique (case-insensitive) |
| `phone` | string | optional, same format as for patients |
| `experience_years` | integer | optional, defaults to 0, maximum 70 |
| `is_available` | boolean | defaults to `true`. If `false`, the doctor can't be assigned to new patients |
| `created_by`, `created_at`, `updated_at` | | read-only |

### Add a doctor

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

### List doctors

`GET /api/doctors/` returns every doctor in the directory.

| Parameter | Example | What it does |
|---|---|---|
| `specialization` | `?specialization=cardio` | case-insensitive partial match |
| `is_available` | `?is_available=true` | filter by availability |
| `min_experience` | `?min_experience=10` | at least that many years |
| `search` | `?search=house` | looks in name and specialization |
| `ordering` | `?ordering=-experience_years` | order by `name`, `experience_years` or `created_at` |

### Get, update or delete one doctor

- `GET /api/doctors/<id>/` is open to any logged-in user
- `PUT` or `PATCH /api/doctors/<id>/` only for the creator, everyone else gets `403`
- `DELETE /api/doctors/<id>/` only for the creator

---

## Mappings

A mapping connects a doctor to a patient. A few rules apply:

- You can only assign doctors to your own patients.
- The same doctor can't be assigned to the same patient twice.
- Doctors marked unavailable can't be assigned.
- A patient can have at most one primary doctor.

### Fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | read-only |
| `patient` | integer | the patient's id, set when you create the mapping |
| `doctor` | integer | the doctor's id, set when you create the mapping |
| `is_primary` | boolean | defaults to `false` |
| `notes` | string | optional, free-text care notes |
| `patient_name`, `doctor_name`, `doctor_specialization` | string | read-only, added so you don't need extra requests |
| `assigned_at` | datetime | read-only |

### Assign a doctor to a patient

`POST /api/mappings/`

```json
{ "patient": 1, "doctor": 3, "is_primary": true, "notes": "Lead physician" }
```

Response, `201 Created`:

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

### List all mappings

`GET /api/mappings/` returns the mappings for your patients. You can filter with `?patient=1`, `?doctor=3` or `?is_primary=true`, search by patient or doctor name with `?search=`, and sort with `?ordering=-assigned_at`.

### See the doctors assigned to one patient

`GET /api/mappings/<patient_id>/` returns the mappings for that patient, and each one includes the doctor's id, name and specialization. If the patient isn't yours you get a `404`.

Heads up: this URL looks the same as the one used to delete a mapping, but here the number is a **patient id**. For `PATCH` and `DELETE` it's a **mapping id**. I kept it this way because the assignment specifies these URLs.

### Update a mapping

`PATCH /api/mappings/<mapping_id>/` can only change `is_primary` and `notes`. The patient and doctor can't be changed, so to reassign you delete the mapping and create a new one.

```json
{ "is_primary": true, "notes": "Moved to lead physician" }
```

If the patient already has a primary doctor, setting another one returns a `400`. Clear the old one first.

### Remove a doctor from a patient

`DELETE /api/mappings/<mapping_id>/` returns `204 No Content`.

---

## Stats

`GET /api/stats/` gives a few summary numbers:

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

The patient and mapping numbers only count your own data. The doctor numbers cover the whole shared directory.