---
title: "Testing Financially-Oriented Web Apps"
type: technique
tags: [web, business-logic, financial, race-conditions, payment, bug-bounty]
created: 2026-08-17
updated: 2026-08-17
sources: []
related: ["[[business-logic-web]]", "[[idor]]"]
status: active
---

# Testing Financially-Oriented Web Apps

## Overview

Applications with financial functionality (e-commerce, fintechs, payment platforms) have specific high-severity attack surfaces with direct impact on money.

## Test categories

### 1. TOCTOU / Race conditions

```
- [ ] Use the same coupon/voucher multiple times simultaneously
- [ ] Make multiple purchases with insufficient balance in parallel
- [ ] Redeem points/cashback multiple times
- [ ] Transfer the same balance to multiple accounts simultaneously
```

**Tools**: Turbo Intruder, Race Condition Repeater (Caido/Burp)

### 2. Parameter manipulation

```
- [ ] Change the price in the request parameters
- [ ] Change quantity to a negative value
- [ ] Manipulate currency (USD -> a weaker currency, unfavorable conversion)
- [ ] Change discount_percentage to values > 100
- [ ] Modify shipping_cost to 0 or negative
- [ ] Change tax_rate
```

**Example**:
```http
POST /api/checkout HTTP/1.1
{
  "item_id": "123",
  "quantity": -1,      <- negative value = credit instead of debit
  "price": 0.01,       <- alter the price
  "currency": "VND"    <- lower-value currency
}
```

### 3. Replay attacks

```
- [ ] Reuse an already-processed payment token
- [ ] Repeat a transfer request with the same idempotency key
- [ ] Capture and reuse a confirmed payment webhook
- [ ] Replay an already-used gift card
```

### 4. Rounding and numeric processing

```
- [ ] Exploit rounding for fractional gain (e.g. 0.009 -> 0.01 in a loop)
- [ ] Test very small values (0.001) or very large ones
- [ ] Integer overflow in monetary values
- [ ] Float precision attacks (0.1 + 0.2 != 0.3)
```

### 5. Payment and payment card

```
- [ ] Test with invalid card numbers (validation bypass)
- [ ] Test with a test-card BIN in production
- [ ] Manipulate CVV/expiry after the initial authorization
- [ ] Charge more than authorized
- [ ] Refund more than the original amount paid
```

### 6. Dynamic pricing / referral programs

```
- [ ] Abuse referral codes infinitely with temporary emails
- [ ] Self-promote via your own referral code
- [ ] Manipulate cashback_percentage
- [ ] Combine multiple discounts that should not stack
```

### 7. Discount codes / vouchers / gift cards

```
- [ ] Enumerate discount codes (SAVE10, PROMO20, etc.)
- [ ] Test gift cards with value 0 -> check whether accepted
- [ ] Apply multiple coupons simultaneously
- [ ] Transfer a gift card to your own account after purchase
- [ ] Expiry bypass (modify the date in the request)
```

### 8. Cryptography and backend/API

```
- [ ] Check whether amount is signed/verified server-side
- [ ] Test a webhook callback without signature validation
- [ ] Analyze whether a payment token is reusable across users
- [ ] Verify that payment is confirmed before releasing the product
```

### 9. Currency arbitrage / deposit-refund

```
- [ ] Deposit in a weak currency -> convert -> withdraw in a strong currency
- [ ] Deposit -> take advantage of a promotion -> withdraw before the lock
- [ ] Abuse a deposit bonus
```

## Impact

- **Critical**: Real financial gain without payment (CVSS 9.0+)
- **High**: Race condition in transfers (balance duplication)
- **Medium**: Price manipulation (CVSS 6.0-7.9)

## Tools

| Tool | Use |
|------|-----|
| Turbo Intruder | Race conditions in payments |
| Caido/Burp Replay | Manual parameter manipulation |
| Caido Automate / Intruder | Fuzzing of discount codes |

## References

- [[business-logic-web]]
- [[idor]]
