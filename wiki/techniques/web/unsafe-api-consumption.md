---
title: "Unsafe Consumption of APIs"
type: technique
tags: [api, unsafe-consumption, supply-chain, third-party, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[ssrf]]"]
status: draft
severity_range: "MEDIUM-CRITICAL"
---

# Unsafe Consumption of APIs

Complements [[api-security]] and the `hunt-api` skill. Focus here is the trust boundary with third-party APIs.

## Overview

This occurs when an application blindly trusts external APIs without adequate validation, authentication, or security controls. Over-trusting third-party APIs can introduce injection attacks, data-integrity compromise, MITM attacks, and insecure redirections. It is essentially a supply-chain attack vector.

## Impact

- Data breaches via a compromised external API
- Injection attacks (SQLi, XSS, RCE) via malicious data from a third-party API
- MITM attacks on unencrypted communications with external APIs
- Phishing via insecure redirections
- Compromise of the system's data integrity

## Where to look

- Integrations with third-party APIs (payment, weather, maps, social media)
- Webhooks and callbacks that receive external data
- Endpoints accepting URLs to fetch resources (images, documents) - see [[ssrf]]
- HTTP (non-TLS) communications with external APIs
- Automatic redirections based on API responses

## Test methodology

1. **Identify integrations**: map every external API consumed.
2. **Check validation**: test whether external API responses are validated before processing.
3. **Test MITM**: verify that communications use HTTPS/TLS.
4. **Test redirections**: verify that redirections are not followed blindly.
5. **Injection via external data**: inject malicious payloads simulating a response from a compromised API.

## Payloads

### Redirect manipulation
```
# If the API follows redirects:
http://evil.com/callback -> redirects to a phishing page
```

### Data integrity
```json
# Simulate a malicious response from an external API:
{"temperature": "<script>alert('xss')</script>"}
{"price": "0.001", "currency": "USD"}  # Price manipulation
```

## Real examples

- A compromised weather API injecting false data, causing panic.
- A currency-conversion banking API with values altered via MITM.
- A payment-gateway redirect modified to point at a phishing page.

## Report tips

- Demonstrate the chain: external API -> malicious data -> impact on the system.
- Evidence the lack of validation of external responses.
- Recommend: enforced TLS, input validation on third-party data, a domain allowlist.
