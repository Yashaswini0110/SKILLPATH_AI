# Manager / HR analytics (Phase 23)

Read-only aggregates. Department is the team scope. There is no
manager-report field.

```text
Employees in department or org
        ↓
Skill-level bands, gap counts, path/quiz participation
```

`GET /api/v1/analytics` is allowed for `MANAGER`, `HR_ADMIN`, and
`SYSTEM_ADMIN`.

- Manager: own department only. Profile must have a department.
- HR / system admin: organization, or `?department=` to slice
- Response never includes names, emails, user IDs, or evidence text
- GitHub is not collected
- Not a hiring or employment prediction
