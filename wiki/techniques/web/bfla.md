---
title: "Broken Function Level Authorization (BFLA)"
type: technique
tags: [api, bfla, authorization, privilege-escalation, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[bola]]", "[[bopla-mass-assignment]]", "[[improper-asset-management]]"]
status: draft
severity_range: "HIGH-CRITICAL"
---

# Broken Function Level Authorization (BFLA)

Complements [[api-security]] and the `hunt-api` skill. Focus here is the function-authorization test.

## Overview

BFLA occurs when an API fails to enforce proper access control at the function/action level. Unlike BOLA (object access), BFLA lets users execute **functions** beyond their privileges, such as a regular user performing admin actions (vertical privilege escalation) or reaching another peer group's functions (lateral movement).

## Impact

- Privilege escalation: regular user executing admin functions
- Lateral movement: reaching another group's or department's functionality
- Mass deletion or modification of data
- Unauthorized creation of admin accounts
- Full system compromise if critical functions are reachable

## Where to look

- Administrative endpoints: `/admin/`, `/api/admin/`, `/api/manage/`
- User management endpoints: `/api/users/delete`, `/api/users/create`
- Configuration functions: `/api/settings/`, `/api/config/`
- Reporting/analytics endpoints: `/api/reports/`, `/api/analytics/`
- Any endpoint with privileged actions (delete, create-user, change-role, export-data)

## Test methodology

1. **Map roles and functions**: identify which functions each role should access.
2. **Hit admin endpoints as a regular user**: reach /admin/ endpoints with a user token.
3. **Manipulate HTTP methods**: if DELETE is blocked, try PUT/PATCH/POST on the same resource.
4. **Test lateral functions**: as a group A user, try to execute group B's functions.
5. **Modify role parameters**: send `role=admin` in update requests.
6. **Test session handling**: use tokens from different sessions for privileged functions.

## Payloads

### Vertical privilege escalation
```
POST /admin/create-user           # With a regular user token
DELETE /admin/delete-user/5502    # With a regular user token
PUT /api/user/role?role=admin     # Modify your own role
POST /api/admin/reset-password    # Without admin authentication

# Swap HTTP methods:
POST /api/user/5502  ->  DELETE /api/user/5502
GET /api/user/5502   ->  PUT /api/user/5502
```

### Lateral movement
```
# As partner A, reach partner B's resources:
GET /api/partners/B/resources
POST /api/partners/B/create-order
```

### Admin function discovery
```
/admin, /api/admin, /api/v1/admin
/api/users/create, /api/users/delete
/api/settings, /api/config
/api/export, /api/backup
/api/logs, /api/audit
```

## Common bypasses

- Swap the HTTP method (POST -> DELETE, GET -> PUT) to reach hidden functions.
- Add `/admin/` to the path of existing endpoints.
- Use headers like `X-Original-URL` or `X-Rewrite-URL` to bypass path-based ACLs.
- Test older API versions that may have weaker authorization.
- Path encoding (%2f for /, double encoding).

## BOLA vs BFLA

| Aspect | BOLA | BFLA |
|--------|------|------|
| What fails | **Object** authorization | **Function/action** authorization |
| Question | "Is this data mine?" | "Am I allowed to run this function?" |
| Example | `GET /api/user/9` returns another user's data | `POST /admin/create-user` as a regular user |
| Typical escalation | Access to other users' data | Privilege escalation (user->admin) or lateral (groupA->groupB) |
| Key test | Swap the object ID | Swap the HTTP method / reach an admin endpoint |

See [[bola]] for the object side.

## Real examples

- Regular user runs DELETE /api/user/5502, deleting another user's account.
- POST /admin/create-user reachable without a role check -> creation of an admin account.
- Swapping POST for DELETE on the same endpoint allows unauthorized deletion.
- PUT /user/role with role=admin accepted for a regular user.
- A legacy API version (`/v1`, `/v2`) may expose functions without the newer version's RBAC -> see [[improper-asset-management]].

## Report tips

- Clearly distinguish BFLA from BOLA: BFLA = unauthorized functions, BOLA = unauthorized objects.
- Demonstrate the full chain: request as a regular user -> admin function execution -> result.
- Include the BOLA vs BFLA table to avoid triager confusion.
- State whether it is vertical (user->admin) or lateral (groupA->groupB).
- Recommend: deny by default, centralized RBAC, an authorization check on every function.
