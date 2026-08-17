---
title: "CAPTCHA Bypass"
type: technique
tags: [captcha, bypass, rate-limit, brute-force, automation]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[access-control]]"]
status: active
---

# CAPTCHA Bypass

## Overview

CAPTCHAs protect against automation/bots. They can be defeated through implementation weaknesses.

## Bypass techniques

### 1. CAPTCHA response not validated server-side
```
# Frontend validates the CAPTCHA but the backend does not verify the token
# Simply remove the captcha field from the request
# Or use an old/invalid CAPTCHA token
POST /login: username=a&password=b&captcha_token=OLD_TOKEN
```

### 2. Reusable token
```
# Solve the CAPTCHA once, reuse the token across multiple requests
# Check whether the token expires or is invalidated after use
```

### 3. Predictable / hard-coded response
```
# Image CAPTCHA with a limited set of answers
# Debug endpoint that returns the answer
# JS source exposes the answer
```

### 4. Audio CAPTCHA
```
# Request the audio version -> use speech-to-text
# 2captcha / CapMonster (solving services)
```

### 5. Solving services
```
# 2captcha.com, anti-captcha.com, CapMonster
# Integrate into automation to solve reCAPTCHA v2/v3
# reCAPTCHA v3: score-based -> can be manipulated with user simulation
```

### 6. Removable parameter
```
# Test without the CAPTCHA parameter:
# captcha_token -> remove it
# g-recaptcha-response -> remove or empty it
POST /register
{"user": "a", "pass": "b"}  # no captcha_token
```

### 7. CAPTCHA fixation
```
# Obtain a CAPTCHA token from one domain and use it on another
# (rare, but happens in custom implementations)
```

### 8. Response manipulation
```
# Intercept the response from the CAPTCHA validation server
# {"valid": false} -> {"valid": true}
```

## Impact
- **High**: bypass of anti-brute-force protection -> credential stuffing, account takeover
- **Medium**: automation of limited actions (spam, scraping)
- **Low**: bypass of informational protection
