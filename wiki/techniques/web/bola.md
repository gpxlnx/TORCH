---
title: "Broken Object Level Authorization (BOLA)"
type: technique
tags: [api, bola, idor, authorization, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[idor]]", "[[bfla]]", "[[bopla-mass-assignment]]"]
status: draft
severity_range: "MEDIUM-CRITICAL"
---

# Broken Object Level Authorization (BOLA)

Complements [[api-security]] and the `hunt-api` skill. Focus here is the object-authorization test, not generic API basics.

## Overview

BOLA (also known as IDOR, Insecure Direct Object Reference) is the #1 vulnerability in the OWASP API Security Top 10. It occurs when an API fails to verify that the authenticated user is allowed to access the specific object being requested. Attackers manipulate object identifiers (IDs) in requests to read, modify, or delete other users' data.

## Impact

- Unauthorized access to other users' data (PII, financial, medical)
- Modification or deletion of other users' data
- Account takeover via BOLA in password reset
- Privilege escalation if admin accounts are reachable
- Confidentiality and integrity breach

## Where to look

- Any endpoint with a user ID: `/api/users/{id}`, `/api/profile/{id}`
- Order/transaction endpoints: `/api/orders/{id}`, `/api/transactions/{id}`
- Document/file endpoints: `/api/documents/{id}`, `/api/files/{id}`
- Password reset: `/api/reset-password/{user_id}`
- Any parameter referencing an object: `?user_id=`, `?account_id=`, `?order_id=`

## Test methodology

1. **Create two test accounts** (Account A and Account B).
2. **Map all endpoints** that accept object identifiers.
3. **Authenticate as Account A** and capture requests carrying A's IDs.
4. **Swap the IDs** to Account B's while keeping A's token.
5. **Verify access**: if B's data comes back, BOLA is confirmed.
6. **Test write operations**: PUT/PATCH/DELETE with another user's ID.
7. **Test ID formats**: sequential, partial UUIDs, encoded IDs.

## Payloads

### ID manipulation
```
# If your ID is 5501, test:
GET /api/users/5502
GET /api/users/5500
GET /api/users/1          # Admin is frequently ID 1

# In query params:
GET /api/profile?id=5502
GET /api/orders?user_id=5502

# In body:
PUT /api/users {"user_id": 5502, "email": "attacker@evil.com"}
DELETE /api/users/5502

# Path traversal in IDs:
GET /api/users/5501/../5502
```

### Password reset BOLA
```
POST /api/reset-password
{"user_id": 5502, "new_password": "hacked123"}
```

## Common bypasses

- Test IDs in different formats (integer, string, UUID, base64-encoded).
- Use different HTTP methods (if GET is protected, try POST/PUT).
- Test additional headers (X-User-Id, X-Account-Id).
- Older API versions may have weaker authorization (/v1/ vs /v3/).
- Test IDs in the body when path params are protected.

## Real examples

- Swapping `user_id=5501` to `user_id=5502` returns another user's full profile.
- PUT /api/reset-password with another user's user_id enables account takeover.
- GET /api/orders/12345 with another user's token returns order details.
- Iterating sequential IDs (1-10000) to extract every user's data.

## Report tips

- Demonstrate with two accounts: the original request and the ID-swapped request.
- Include screenshots of responses showing different users' data.
- Calculate impact scale: if IDs are sequential, how many users are affected.
- State whether it is read-only (GET) or read-write (PUT/DELETE); write is more severe.
- Recommend: random UUIDs, an authorization check on every request, a zero-trust policy.
