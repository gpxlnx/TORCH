---
title: "Unrestricted Resource Consumption"
type: technique
tags: [api, dos, rate-limiting, resource-abuse, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[unrestricted-business-flows]]"]
status: draft
severity_range: "LOW-HIGH"
---

# Unrestricted Resource Consumption

Complements [[api-security]] and the `hunt-api` skill. Focus here is resource-limit abuse.

## Overview

This occurs when an API allows excessive use of resources (CPU, memory, bandwidth, storage) without adequate limits. Attackers exploit the absence of rate limiting, upload restrictions, execution timeouts, and pagination controls to cause DoS, inflate operating costs, or distract security teams.

## Impact

- Denial of Service (DoS/DDoS): the API becomes unavailable to legitimate users
- Sharp increase in operating cost in pay-as-you-go cloud environments
- Performance degradation for all users
- Distraction cover for more serious attacks (data exfiltration during a DoS)

## Where to look

- Search/listing endpoints with pagination parameters (page_size, limit, max_return)
- File-upload endpoints without a size restriction
- Endpoints processing complex queries (search, filter, aggregate)
- Login/registration endpoints without rate limiting
- Endpoints with recursive processing (JSON/XML parsing)
- APIs with a pay-as-you-go model

## Test methodology

1. **Rate-limit check**: send 100+ rapid requests to check for limits.
2. **Pagination abuse**: change page_size/limit to extreme values (1, 10000, 999999).
3. **File-upload test**: send a file larger than expected.
4. **Recursive payload**: send deeply nested JSON.
5. **Concurrent requests**: send multiple simultaneous requests.
6. **Long-running query**: send a complex query and measure response time.

## Payloads

### Pagination abuse
```
GET /api/users?page_size=20000
GET /api/search?limit=999999&page=1
GET /api/products?max_return=100000
```

### Recursive JSON
```json
{"a":{"b":{"c":{"d":{"e":{"f":{"g":{"h":{"i":{"j":"deep"}}}}}}}}}}
```

### Large file upload
```bash
# Generate a 500MB file
dd if=/dev/zero of=large_file bs=1M count=500
# Upload to the endpoint
curl -X POST -F "file=@large_file" https://target/api/upload
```

## Common bypasses

- Distribute requests across multiple IPs to bypass IP-based rate limiting.
- Use X-Forwarded-For headers with different IPs.
- Alternate between similar endpoints to evade per-endpoint rate limiting.
- Use multiple API keys or accounts.

## Real examples

- Changing max_return from 250 to 20000, producing a multi-MB response and slowdown.
- An API without rate limiting on the login endpoint allowing unlimited brute force.
- A 500MB file upload against an API whose 10MB limit is not enforced.
- A public API abused by bots for mass scraping before rate limiting was implemented.

## Report tips

- Demonstrate measurable impact: normal response time vs response time with an abusive payload.
- Include potential cost calculations for cloud environments.
- Show the absence of rate limiting with evidence (X requests without blocking).
- Recommend: per-user/IP rate limiting, pagination with enforced limits, execution timeouts.
