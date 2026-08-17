---
title: "API Key Management - Security and Testing"
type: technique
tags: [api, api-key, secrets, information-disclosure, bug-bounty]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[secrets-exposure]]", "[[api-key-exposure]]", "[[api-security]]"]
status: active
---

# API Key Management - Security and Testing

## Overview

API keys are credentials that authenticate API clients. Misconfigurations and leaks are extremely common and usually result in unauthorized access to APIs, sensitive data, or privileged actions.

## Where API keys leak

### Common leak sources

```
1. JavaScript bundles (client-side)
2. APK/IPA (mobile apps)
3. Public git repositories (.env, config files)
4. Published Postman collections
5. Exposed Swagger/OpenAPI specs
6. Error responses with stack traces
7. HTTP responses with internal headers
8. Reachable config files (/config.json, /api-config.js)
9. Source maps
10. Google Dorking
```

### How to find via recon

```bash
# JavaScript bundles
# Use LinkFinder, JSluice, or grep
grep -r "api[_-]?key\|apikey\|api_secret\|access_token\|bearer" --include="*.js" .

# Google dork
site:target.com filetype:js "api_key"
site:target.com "Authorization: Bearer"

# GitHub
"target.com" "api_key" OR "apikey" OR "secret"

# Wayback Machine
gau target.com | grep -i "\.env\|config\|api"
```

## Testing found API keys

### API key validation

```bash
# Test whether it is still active
curl -H "Authorization: Bearer <KEY>" https://api.target.com/v1/me

# Test scope/permissions
curl -H "X-API-Key: <KEY>" https://api.target.com/v1/admin/users

# Check whether it works cross-environment
curl -H "Authorization: Bearer <KEY>" https://api-staging.target.com/v1/me
```

### Check scope and privileges

```bash
# Test administrative endpoints
for endpoint in /admin /users /config /internal /debug; do
  curl -s -o /dev/null -w "%{http_code} $endpoint\n" \
    -H "Authorization: Bearer <KEY>" \
    "https://api.target.com/v1$endpoint"
done
```

## Token analysis via a Sequencer

### Check API-key randomness

1. **Capture** 100+ distinct tokens.
2. **Proxy -> Sequencer -> Live Capture** (Burp) or equivalent.
3. **Analyze entropy**: if < 50 bits -> weak.
4. **Patterns**: check for predictable components (timestamp, UUID v1, etc.).

```bash
# Manual entropy analysis
cat tokens.txt | awk '{print length, $0}' | sort -n  # check consistent length
cat tokens.txt | sort | uniq -d  # detect reuse
```

## JWT attacks

### Attack types

```bash
# 1. None Algorithm Attack
jwt_tool <TOKEN> -X n

# 2. Algorithm Switch (RS256 -> HS256)
jwt_tool <TOKEN> -X a

# 3. JWT Crack (brute force secret)
crunch 5 5 -o wordlist.txt
jwt_tool <TOKEN> -C -d wordlist.txt

# 4. jwks.json spoofing
jwt_tool <TOKEN> -X s
```

## API key rotation testing

```bash
# If a key can be rotated, check:
# 1. Does the old key still work after rotation?
# 2. Is there a limit on rotation speed?
# 3. Is there a notification when the old key is used?
POST /api/v1/keys/rotate
Authorization: Bearer <CURRENT_KEY>
```

## Impact

| Type | Impact | CVSS |
|------|--------|------|
| Exposed API key with read access | Information disclosure | 5.0-7.0 |
| API key with admin access | Privilege escalation | 8.0-9.0 |
| API key for a critical service (AWS, Stripe) | Critical | 9.0+ |
| JWT without a valid signature | Auth bypass | 8.5-9.5 |

## References

- [[secrets-exposure]]
- [[api-key-exposure]]
- [[api-security]]
