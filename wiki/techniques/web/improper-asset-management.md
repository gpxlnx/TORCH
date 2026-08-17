---
title: "Improper Asset Management in APIs"
type: technique
tags: [api, asset-management, shadow-api, zombie-api, versioning, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[bola]]"]
status: draft
severity_range: "MEDIUM-CRITICAL"
---

# Improper Asset Management in APIs

Complements [[api-security]] and the `hunt-api` skill. Focus here is finding forgotten and legacy endpoints.

## Overview

Improper Asset Management occurs when organizations fail to track, update, or retire API endpoints, leaving forgotten, undocumented, or deprecated APIs reachable. Three main categories: **Shadow APIs** (undocumented), **Zombie APIs** (deprecated but still live), and **Untracked API Versions** (old versions without patches).

## Impact

- Increased attack surface from unprotected endpoints
- Unauthorized access via APIs without adequate authentication
- Data exposure via APIs with unpatched vulnerabilities
- Compliance violations (GDPR, CCPA) via APIs exposing customer data

## Where to look

- Prior API versions: `/v1/`, `/v2/` when `/v3/` is current
- Dev/test environments: `/alpha/`, `/beta/`, `/uat/`, `/test/`, `/demo/`, `/staging/`
- Debug endpoints: `/debug`, `/api/debug`, `/api/internal`
- Changelogs and release notes mentioning fixed vulnerabilities
- Dev subdomains: dev.api.target.com, staging.api.target.com
- Outdated documentation referencing old endpoints

## Test methodology

1. **Version enumeration**: test /v1/, /v2/ for each documented endpoint.
2. **Environment guessing**: test /test/, /demo/, /alpha/, /beta/, /uat/, /staging/.
3. **Changelog analysis**: analyze changelogs to find vulns fixed in newer versions.
4. **Subdomain enumeration**: look for dev/staging subdomains.
5. **Documentation review**: compare documented endpoints against live endpoints.
6. **Endpoint fuzzing**: brute-force common internal API paths.

## Payloads

### Version testing
```
/api/v1/users, /api/v2/users, /api/v3/users
/api/v1/admin, /api/v2/admin
/v1/auth, /v2/auth
```

### Environment discovery
```
/api/test/users, /api/demo/users
/api/alpha/users, /api/beta/users
/api/uat/users, /api/staging/users
/api/debug, /api/internal
/api/health, /api/status, /api/metrics
```

### Subdomain patterns
```
dev.api.target.com
staging.api.target.com
test.api.target.com
internal.api.target.com
```

## Real examples

- /v1/auth without strong authentication while /v2/auth has OAuth implemented.
- /api/debug publicly reachable, exposing database credentials and API keys.
- /v1/transfer in a banking API still live, allowing transactions without security patches.
- A changelog revealing "Fixed SQL injection in v1 admin endpoint" -> v1 still vulnerable.

## Report tips

- Compare functionality/security between the old version and the current version.
- Demonstrate that the old version has vulnerabilities fixed in the new one.
- Include evidence that the endpoint is live and responds.
- Recommend: an API inventory, a deprecation process, an API gateway with version control.
