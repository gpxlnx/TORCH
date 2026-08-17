---
title: "IDN Homograph Attack"
type: technique
tags: [idn, homograph, unicode, phishing, email, spoofing]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[open-redirect]]"]
status: active
---

# IDN Homograph Attack

## Overview

IDN (Internationalized Domain Names) allow unicode characters in domains. Characters that look visually identical but have different code points ("homographs") make it possible to create domains that resemble legitimate ones.

## Homograph examples

```
Unicode character -> looks like
a (Cyrillic a, U+0430) -> a (Latin a)
e (Cyrillic e, U+0435) -> e
i (Cyrillic i, U+0456) -> i
o (Cyrillic o, U+043E) -> o
i (Dotless I, U+0131) -> i
fi (Latin ligature fi, U+FB01) -> fi
(Full-width forms) -> google

# Homograph domain:
xn--pple-43d.com = apple.com (Cyrillic a)
# Modern browsers display the punycode form, but applications may not
```

## Use in bug bounty

### 1. Email normalization bypass
```
# Register with a homograph of the victim's email
victim@target.com  # Cyrillic i
VICTIM@TARGET.COM  # different case normalization

# If the system normalizes differently:
# victim@target.com == victim@target.com (homograph) -> ATO
```

### 2. Account takeover via registration
```
# Find a system that:
# 1. Accepts unicode in emails
# 2. Compares without normalizing unicode
# 3. Creates a separate account for the homograph email

# Register: adm!n@target.com (exclamation resembling i in some fonts)
# Or: victim@target.com vs victim@target.com (dotless i)
```

### 3. Custom SSO with homograph
```
# SSO that trusts the email returned by the provider
# Create an account at the provider with a homograph email
# SSO creates a new account OR accesses the existing one -> ATO
```

## Detection

```python
# Check whether the system accepts unicode characters in email fields
# Test: normal email vs visually identical homograph
# Check the response: duplicate error -> normalizes correctly
#                     successful login -> vulnerable

import unicodedata
# Normalize: unicodedata.normalize('NFKD', email).encode('ascii', 'ignore')
```

## Impact
- **Critical**: Account Takeover via homograph email in SSO
- **High**: Phishing with an indistinguishable domain
- **Medium**: Bypass of domain allowlists/blocklists
