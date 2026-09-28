# Phase 1 API

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

All JSON endpoints under `/api/v1` use the envelope:

```json
{ "data": {}, "message": null }
```

Errors:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": []
  }
}
```

Authenticated routes require `Authorization: Bearer <access_token>`.

## Health

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/health` | No |

## Auth

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/register` | No | Create user + employee profile |
| POST | `/api/v1/auth/login` | No | Issue access and refresh tokens |
| POST | `/api/v1/auth/refresh` | No | Rotate access token |
| POST | `/api/v1/auth/logout` | Yes | Revoke refresh token |
| GET | `/api/v1/auth/me` | Yes | Current user |

Register body:

```json
{
  "email": "alex@example.com",
  "password": "Str0ngPass",
  "full_name": "Alex Johnson",
  "role": "EMPLOYEE"
}
```

`role` must be one of `EMPLOYEE`, `MANAGER`, `MENTOR`, `HR_ADMIN`, `SYSTEM_ADMIN`.

## Employee profile

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/employees/me` | Profile, completeness, nested collections |
| PUT | `/api/v1/employees/me` | Update profile fields and target role |

## Education

| Method | Path |
| --- | --- |
| GET | `/api/v1/employees/me/education` |
| POST | `/api/v1/employees/me/education` |
| PUT | `/api/v1/employees/me/education/{education_id}` |
| DELETE | `/api/v1/employees/me/education/{education_id}` |

## Work experience

| Method | Path |
| --- | --- |
| GET | `/api/v1/employees/me/experience` |
| POST | `/api/v1/employees/me/experience` |
| PUT | `/api/v1/employees/me/experience/{experience_id}` |
| DELETE | `/api/v1/employees/me/experience/{experience_id}` |

## Skills

| Method | Path |
| --- | --- |
| GET | `/api/v1/skills` | Catalog |
| GET | `/api/v1/employees/me/skills` |
| POST | `/api/v1/employees/me/skills` |
| PUT | `/api/v1/employees/me/skills/{employee_skill_id}` |
| DELETE | `/api/v1/employees/me/skills/{employee_skill_id}` |

Self-declared proficiency is 1–5. Confidence for self-declaration is stored as a low default and labeled as self-reported. It is not verified skill evidence.

## Target roles

| Method | Path |
| --- | --- |
| GET | `/api/v1/roles` |
| GET | `/api/v1/roles/{role_id}` |
