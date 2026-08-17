---
title: "Response Manipulation"
type: technique
tags: [response-manipulation, intercept, status-code, bypass, admin-panel, web, bug-bounty]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related:
  - "[[bypass-403-401]]"
  - "[[idor]]"
status: active
---

# Response Manipulation

## Overview

Response manipulation is intercepting and modifying an HTTP response before the browser processes it. The goal is bypassing client-side controls: forced redirects, status-code checks, and access restrictions enforced only in the front-end.

## Impact

- **Medium**: bypass UI restrictions (e.g. view premium page content without paying).
- **High**: bypass client-side authentication, reach admin panels gated only by a redirect.
- **Critical**: chained with another bug (IDOR, SQLi) reached via the unauthorized access.

## Where to look

- **301/302 redirects** to login: change to 200 and read the real content.
- **403 Forbidden** responses: change to 200 and check whether a body is returned.
- **JSON `"success": false`**: flip to `true`.
- **JSON `"role": "user"`**: flip to `"admin"`.
- **Admin panels** protected only by a front-end redirect.
- **`"authenticated": false`**: flip to `true`.

## Test methodology

### 1. Intercept responses (Caido)

Use Caido Match/Replace (Tamper) to rewrite responses automatically, or intercept manually and edit the status line/body. A rule matching `30[12]` status or an `/admin` URL is a good start; see [[caido]].

### 2. Intercept and modify

```http
# Original response
HTTP/1.1 302 Found
Location: /login

# Modified
HTTP/1.1 200 OK

# Or in JSON
{"success": false, "role": "user"}
# Modified
{"success": true, "role": "admin"}
```

### 3. Find admin panels by path brute force

```bash
subfinder -duc -silent -d target.com -all | \
  httpx -duc -sc -mc 200 -title -td -cl -ct -t 50 \
  -path admin-panel-paths.txt | awk '!seen[$3]++'
```

## Common techniques

### Swap 302 for 200

Server returns a 302 redirect to login; change the status to 200 before the browser processes it:

```
Original:  HTTP/1.1 302 Found | Location: /login
Manipulated: HTTP/1.1 200 OK
```

### Swap 403 for 200

```
HTTP/1.1 403 Forbidden -> HTTP/1.1 200 OK
```

### Modify JSON body

```json
// Original
{"authenticated": false, "redirect": "/login"}

// Manipulated
{"authenticated": true, "redirect": null}
```

### Strip security headers

```http
# Remove Content-Security-Policy to ease XSS
# Remove X-Frame-Options for clickjacking
# Drop httponly on cookies
```

## Limitations

- Works only when authorization logic lives client-side.
- Does not bypass real server-side auth (the API still validates).
- Useful to discover admin interfaces; the actions may still fail if the API validates tokens.

## Reporting tips

- Show that admin content is reachable without valid authentication.
- Show the authorization was enforced client-side only.
- If the API also returns sensitive data, escalate to High/Critical.
- Combine with [[idor]] if the returned data belongs to other users.

## Tools

- Caido Match/Replace (Tamper) to automate response rewrites; see [[caido]].
- Manual intercept + edit for one-off checks.
