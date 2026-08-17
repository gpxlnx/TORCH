---
title: "Unrestricted Access to Sensitive Business Flows"
type: technique
tags: [api, business-flows, automation-abuse, bot-protection, owasp-api-top10]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[api-security]]", "[[business-logic-web]]", "[[unrestricted-resource-consumption]]"]
status: draft
severity_range: "MEDIUM-HIGH"
---

# Unrestricted Access to Sensitive Business Flows

Complements [[api-security]] and the `hunt-api` skill. This is the OWASP API "scale abuse" class, distinct from a logic flaw.

## Overview

Unlike business-logic vulnerabilities (which exploit flaws in the logic), this vulnerability occurs when APIs expose critical business functions without sufficient restrictions against **abuse at scale**. Legitimate users or bots can overuse features such as ticket purchasing, coupon application, or trial-account creation, causing financial loss and operational disruption. The problem here is SCALE, not LOGIC.

## Impact

- Direct commercial losses (ticket scalping, coupon abuse)
- Operational disruption (services unavailable to legitimate users)
- Market manipulation (trading bots)
- Business-model abuse (free-trial abuse)
- Reputational damage and loss of trust

## Where to look

- Purchase/reservation endpoints (tickets, products, services)
- Coupon/discount-code application
- Account creation (free trial, registration)
- Trading/financial-transaction APIs
- Voting/rating endpoints
- Any operation that should have per-user or per-session limits

## Test methodology

1. **Identify critical business flows**: map high-value operations.
2. **Test limits**: check for per-user, per-IP, per-session limits.
3. **Automation**: script a rapid repeat of the operation.
4. **Multi-account**: create multiple accounts to test per-account limits.
5. **Bot detection**: check whether CAPTCHA or behavior analysis exists.
6. **Parallel sessions**: test multiple simultaneous sessions.

## Payloads

### Automation scripts
```python
# Mass automated purchase
for i in range(1000):
    requests.post("/api/purchase", json={"item_id": "ticket", "qty": 10})

# Account creation for free-trial abuse
for i in range(100):
    requests.post("/api/register", json={"email": f"user{i}@temp.com"})
```

### Coupon reuse
```json
POST /api/cart/apply-coupon {"code": "WELCOME50"}
# Repeat N times in the same session
# Test with new sessions
# Test with different accounts
```

## Real examples

- Bots buying thousands of concert tickets in seconds, ahead of humans.
- A welcome coupon used unlimited times by the same account.
- Creation of 100 fake accounts for infinite streaming free trials.
- Trading bots executing thousands of micro-transactions to manipulate prices.

## Report tips

- Demonstrate the abuse scale (N operations in X seconds with no blocking).
- Calculate potential financial impact.
- Distinguish from a business-logic bug: here the problem is SCALE, not LOGIC.
- Recommend: rate limiting, CAPTCHA, behavior analysis, per-user limits.
